"""
Módulo de Testes Unitários de Conformidade Trabalhista e Previdenciária.

Testa os cenários normativos de rescisão:
- Demissão sem justa causa com aviso prévio proporcional (Lei 12.506/2011)
- Pedido de demissão com desconto de aviso prévio (Art. 487, § 2º CLT)
- Demissão por justa causa e preservação de férias vencidas (Súmula 171 TST)
- Acordo consensual da Reforma Trabalhista (Art. 484-A CLT)
- Exatidão da tabela progressiva de INSS e IRRF
"""

import unittest
from datetime import date
from decimal import Decimal

from rescisao_trabalhista.enums import TipoRescisao, TipoAvisoPrevio
from rescisao_trabalhista.models import DadosContrato
from rescisao_trabalhista.tabelas import TabelaINSS, TabelaIRRF, moeda
from rescisao_trabalhista.calculadora import CalculadoraRescisao


class TestTabelasTributarias(unittest.TestCase):
    """Valida o cálculo do INSS progressivo e do IRRF com desconto simplificado."""

    def test_inss_faixa_1(self):
        # Base de R$ 1.412,00 na 1ª faixa (7,5%) -> 1412 * 0.075 = 105.90
        imposto, alq, _ = TabelaINSS.calcular_contribuicao(Decimal("1412.00"))
        self.assertEqual(imposto, Decimal("105.90"))

    def test_inss_faixa_superior_progressiva(self):
        # Base de R$ 3.000,00:
        # Faixa 1 (0 a 1412.00): 1412.00 * 0.075 = 105.90
        # Faixa 2 (1412.00 a 2666.68): (2666.68 - 1412.00) = 1254.68 * 0.09 = 112.9212 -> 112.92
        # Faixa 3 (2666.68 a 3000.00): (3000.00 - 2666.68) = 333.32 * 0.12 = 39.9984 -> 40.00
        # Total esperado: 105.90 + 112.92 + 40.00 = 258.82
        imposto, _, _ = TabelaINSS.calcular_contribuicao(Decimal("3000.00"))
        self.assertEqual(imposto, Decimal("258.82"))

    def test_inss_teto(self):
        # Base de R$ 10.000,00 (acima do teto de R$ 7.786,02):
        # Máxima contribuição previdenciária = 908.86
        imposto, _, _ = TabelaINSS.calcular_contribuicao(Decimal("10000.00"))
        self.assertEqual(imposto, Decimal("908.86"))

    def test_irrf_isencao(self):
        # Rendimento de R$ 2.000,00 líquido de INSS -> dentro da faixa de isenção de R$ 2.259,20
        imposto, base, alq, metodo = TabelaIRRF.calcular_imposto(
            rendimento_bruto=Decimal("2000.00"),
            inss_descontado=Decimal("150.00"),
            numero_dependentes=0,
        )
        self.assertEqual(imposto, Decimal("0.00"))


class TestCalculosRescisao(unittest.TestCase):
    """Valida as fórmulas e direitos rescisórios conforme CLT."""

    def test_sem_justa_causa_aviso_indenizado_com_dois_anos_servico(self):
        # Admitido em 01/01/2022, demitido em 01/01/2024 -> exatos 2 anos completos
        # Lei 12.506/2011: 30 dias + (2 * 3) = 36 dias de aviso prévio
        contrato = DadosContrato(
            salario_base=Decimal("3000.00"),
            data_admissao=date(2022, 1, 1),
            data_demissao=date(2024, 1, 10),
            tipo_rescisao=TipoRescisao.SEM_JUSTA_CAUSA,
            tipo_aviso_previo=TipoAvisoPrevio.INDENIZADO,
            saldo_fgts=Decimal("5000.00"),
            ferias_vencidas_periodos=0,
        )
        calc = CalculadoraRescisao(contrato)
        dem = calc.liquidar()

        # Aviso prévio deve ser 36 dias
        self.assertEqual(dem.dias_aviso_previo, 36)

        # Projeção da data final: 10/01/2024 + 36 dias = 15/02/2024
        self.assertEqual(dem.data_projetada, date(2024, 2, 15))

        # 13º Proporcional:
        # Janeiro: 10/01 a 31/01 (22 dias >= 15) -> 1 avo
        # Fevereiro: 01/02 a 15/02 (15 dias >= 15) -> 1 avo
        # Total avos de 13º projetados: 2/12
        self.assertEqual(dem.avos_decimo_terceiro, 2)

        # FGTS: multa rescisória de 40% sobre (5000 + fgts_rescisorio)
        self.assertEqual(dem.fgts.percentual_multa, Decimal("40.00"))
        self.assertTrue(dem.fgts.direito_saque)
        self.assertEqual(dem.fgts.percentual_saque, Decimal("100.00"))

        # Seguro-desemprego habilitado (2 anos de registro)
        self.assertTrue(dem.seguro_desemprego.tem_direito)

    def test_pedido_demissao_aviso_nao_cumprido(self):
        # No pedido de demissão sem cumprimento do aviso, o empregador desconta 30 dias (salário integral)
        salario = Decimal("4000.00")
        contrato = DadosContrato(
            salario_base=salario,
            data_admissao=date(2023, 1, 1),
            data_demissao=date(2023, 6, 30),
            tipo_rescisao=TipoRescisao.PEDIDO_DEMISSAO,
            tipo_aviso_previo=TipoAvisoPrevio.NAO_CUMPRIDO_PELO_EMPREGADO,
            saldo_fgts=Decimal("2000.00"),
        )
        calc = CalculadoraRescisao(contrato)
        dem = calc.liquidar()

        # Verifica se o desconto de 30 dias de aviso prévio está presente
        desc_aviso = next((r for r in dem.rubricas_descontos if r.codigo == "101"), None)
        self.assertIsNotNone(desc_aviso)
        self.assertEqual(desc_aviso.valor, salario)

        # Sem direito a saque nem multa de FGTS
        self.assertFalse(dem.fgts.direito_saque)
        self.assertEqual(dem.fgts.percentual_multa, Decimal("0.00"))
        self.assertFalse(dem.seguro_desemprego.tem_direito)

    def test_demissao_com_justa_causa_e_ferias_vencidas(self):
        # Na justa causa (Art. 482), não há 13º nem férias proporcionais nem aviso prévio,
        # MAS férias vencidas com 1/3 são asseguradas pela Súmula 171 do TST.
        salario = Decimal("3000.00")
        contrato = DadosContrato(
            salario_base=salario,
            data_admissao=date(2022, 1, 1),
            data_demissao=date(2023, 7, 20),
            tipo_rescisao=TipoRescisao.COM_JUSTA_CAUSA,
            tipo_aviso_previo=TipoAvisoPrevio.NAO_APLICAVEL,
            ferias_vencidas_periodos=1,
        )
        calc = CalculadoraRescisao(contrato)
        dem = calc.liquidar()

        # Não deve haver rubrica de 13º proporcional
        rubrica_13 = next((r for r in dem.rubricas_proventos if r.codigo == "003"), None)
        self.assertIsNone(rubrica_13)

        # Não deve haver rubrica de férias proporcionais
        rubrica_fp = next((r for r in dem.rubricas_proventos if r.codigo == "006"), None)
        self.assertIsNone(rubrica_fp)

        # Deve haver férias vencidas (3000.00) e 1/3 (1000.00)
        rubrica_fv = next((r for r in dem.rubricas_proventos if r.codigo == "004"), None)
        rubrica_terco = next((r for r in dem.rubricas_proventos if r.codigo == "005"), None)
        self.assertIsNotNone(rubrica_fv)
        self.assertEqual(rubrica_fv.valor, Decimal("3000.00"))
        self.assertEqual(rubrica_terco.valor, Decimal("1000.00"))

        # FGTS sem multa e sem saque
        self.assertFalse(dem.fgts.direito_saque)
        self.assertEqual(dem.fgts.percentual_multa, Decimal("0.00"))

    def test_acordo_consensual_art_484_a(self):
        # Acordo consensual (Reforma Trabalhista):
        # - Aviso indenizado pela metade (50%)
        # - Multa rescisória do FGTS de 20%
        # - Saque de até 80% do FGTS
        # - Sem seguro-desemprego
        contrato = DadosContrato(
            salario_base=Decimal("3000.00"),
            data_admissao=date(2023, 1, 1),
            data_demissao=date(2023, 6, 15),
            tipo_rescisao=TipoRescisao.ACORDO_CONSENSUAL,
            tipo_aviso_previo=TipoAvisoPrevio.INDENIZADO,
            saldo_fgts=Decimal("4000.00"),
        )
        calc = CalculadoraRescisao(contrato)
        dem = calc.liquidar()

        # Aviso prévio integral seria 30 dias * 100 = 3000; com 50% = 1500.00
        rubrica_aviso = next((r for r in dem.rubricas_proventos if r.codigo == "002"), None)
        self.assertIsNotNone(rubrica_aviso)
        self.assertEqual(rubrica_aviso.valor, Decimal("1500.00"))

        # Multa FGTS deve ser 20%
        self.assertEqual(dem.fgts.percentual_multa, Decimal("20.00"))
        self.assertTrue(dem.fgts.direito_saque)
        self.assertEqual(dem.fgts.percentual_saque, Decimal("80.00"))

        # Sem seguro-desemprego
        self.assertFalse(dem.seguro_desemprego.tem_direito)


if __name__ == "__main__":
    unittest.main()
