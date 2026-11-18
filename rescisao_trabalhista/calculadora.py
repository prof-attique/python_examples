"""
Módulo Central da Calculadora de Rescisão Trabalhista (Motor de Regras CLT).

Implementa a liquidação financeira das obrigações rescisórias trabalhistas
em perfeita observância à Consolidação das Leis do Trabalho (CLT),
à Lei nº 12.506/2011 (Aviso Prévio Proporcional), à Lei nº 8.036/1990 (FGTS),
à Lei nº 4.090/1962 (Gratificação Natalina/13º Salário) e às Súmulas vinculantes
do Tribunal Superior do Trabalho (TST) e Superior Tribunal de Justiça (STJ).

Princípios Arquiteturais e Matemáticos:
1. Ponto Fixo (Decimal): Toda a computação financeira é operada na base Decimal,
   eliminando representações aproximadas de ponto flutuante binário (IEEE 754).
2. Regra Comercial vs Regra Calendário:
   - Saldo de Salário e Diárias: Base comercial de 30 dias (Art. 64 da CLT).
   - Prazos de Projeção e Aniversários Aquisitivos: Contagem estrita em dias corridos de calendário.
3. Regra dos 15 Dias (Fração Legal):
   - 13º Salário: Art. 1º, § 2º da Lei 4.090/1962 (fração >= 15 dias no mês civil).
   - Férias Proporcionais: Art. 146, parágrafo único da CLT (fração >= 15 dias no período aquisitivo).
"""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from rescisao_trabalhista.enums import TipoRescisao, TipoAvisoPrevio
from rescisao_trabalhista.models import (
    DadosContrato,
    RubricaRescisoria,
    ResumoFGTS,
    ResumoSeguroDesemprego,
    DemonstrativoRescisao,
)
from rescisao_trabalhista.tabelas import TabelaINSS, TabelaIRRF, moeda, CENTAVO


class CalculadoraRescisao:
    """
    Motor executivo de liquidação de verbas rescisórias trabalhistas.
    """

    def __init__(self, contrato: DadosContrato):
        self.contrato = contrato
        self._validar_premissas()

    def _validar_premissas(self) -> None:
        """Assegura a consistência das premissas jurídicas e cronológicas de entrada."""
        if self.contrato.data_demissao < self.contrato.data_admissao:
            raise ValueError("A data de demissão/afastamento não pode ser anterior à data de admissão.")
        if self.contrato.salario_base <= Decimal("0.00"):
            raise ValueError("O salário base contratual deve ser estritamente positivo.")

    # -------------------------------------------------------------------------
    # 1. CÔMPUTOS CRONOLÓGICOS E TEMPO DE SERVIÇO
    # -------------------------------------------------------------------------

    @staticmethod
    def calcular_anos_completos(admissao: date, demissao: date) -> int:
        """
        Determina os anos integrais de vínculo empregatício completados até a demissão.
        
        Fundamento: Lei nº 12.506/2011 c/c Nota Técnica nº 184/2012 CGRT/SRT/MTE.
        O adicional de 3 dias de aviso prévio exige o implemento de ano completo de serviço.
        """
        anos = demissao.year - admissao.year
        # Se ainda não atingiu o dia/mês de admissão no ano da demissão, retrocede 1 ano
        if (demissao.month, demissao.day) < (admissao.month, admissao.day):
            anos -= 1
        return max(0, anos)

    @staticmethod
    def calcular_duracao_vinculo(admissao: date, demissao: date) -> Tuple[int, int, int]:
        """
        Calcula o tempo de serviço decomposto em (anos, meses, dias) pelo calendário civil.
        """
        anos = demissao.year - admissao.year
        meses = demissao.month - admissao.month
        dias = demissao.day - admissao.day

        if dias < 0:
            # Empresta dias do mês anterior
            mes_anterior = demissao.month - 1 if demissao.month > 1 else 12
            ano_anterior = demissao.year if demissao.month > 1 else demissao.year - 1
            _, dias_no_mes = monthrange(ano_anterior, mes_anterior)
            dias += dias_no_mes
            meses -= 1

        if meses < 0:
            meses += 12
            anos -= 1

        return max(0, anos), max(0, meses), max(0, dias)

    def calcular_dias_aviso_previo(self, anos_completos: int) -> int:
        """
        Calcula a quantidade de dias devidos a título de aviso prévio.
        
        Fundamento Técnico:
        - Art. 1º, caput da Lei nº 12.506/2011: mínimo de 30 dias.
        - Art. 1º, parágrafo único da Lei nº 12.506/2011: acréscimo de 3 dias por ano completo
          de serviço prestado na mesma empresa, até o máximo de 60 dias adicionais (teto global = 90 dias).
        - Súmula nº 441 do TST: O direito ao aviso proporcional aplica-se apenas às rescisões ocorridas
          após a vigência da referida lei.
        - Nota Técnica 184/2012 CGRT/SRT/MTE: No pedido de demissão, o desconto patronal limita-se
          ao aviso fixo de 30 dias (o acréscimo de 3 dias é prerrogativa exclusiva do empregado).
        """
        if self.contrato.tipo_rescisao in (
            TipoRescisao.COM_JUSTA_CAUSA,
            TipoRescisao.TERMINO_CONTRATO_EXPERIENCIA,
            TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADOR,
            TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADO,
        ):
            return 0

        # No pedido de demissão com desconto do trabalhador, fixa em 30 dias
        if (
            self.contrato.tipo_rescisao == TipoRescisao.PEDIDO_DEMISSAO
            and self.contrato.tipo_aviso_previo == TipoAvisoPrevio.NAO_CUMPRIDO_PELO_EMPREGADO
        ):
            return 30

        # Demissão sem justa causa ou acordo consensual
        adicional = min(60, anos_completos * 3)
        return 30 + adicional

    def projetar_data_final(self, dias_aviso: int) -> date:
        """
        Calcula a data final ficcional do contrato projetada pelo aviso prévio indenizado.
        
        Fundamento Técnico:
        - Art. 487, § 1º da CLT c/c Súmula nº 371 do TST: A projeção do aviso prévio indenizado
          integra o tempo de serviço para todos os efeitos legais (avaliação de avos e anotação na CTPS,
          conforme Orientação Jurisprudencial nº 82 da SDI-1 do TST).
        """
        if (
            self.contrato.tipo_aviso_previo == TipoAvisoPrevio.INDENIZADO
            or self.contrato.tipo_rescisao == TipoRescisao.ACORDO_CONSENSUAL
        ) and dias_aviso > 0:
            return self.contrato.data_demissao + timedelta(days=dias_aviso)
        return self.contrato.data_demissao

    # -------------------------------------------------------------------------
    # 2. CÔMPUTO DE AVOS PROPORCIONAIS (13º E FÉRIAS)
    # -------------------------------------------------------------------------

    @staticmethod
    def calcular_avos_decimo_terceiro(admissao: date, data_projetada: date) -> int:
        """
        Determina os avos (1/12) devidos de gratificação natalina proporcional no ano da rescisão.
        
        Fundamento Legal:
        - Art. 1º, §§ 1º e 2º da Lei nº 4.090/1962: A apuração dá-se dentro do ano civil
          (1º de janeiro a 31 de dezembro).
        - Fração igual ou superior a 15 dias de trabalho no mês civil equivale a 1 mês integral (1 avo).
        - Súmula nº 157 do TST: A projeção do aviso prévio indenizado é computada no 13º salário.
        """
        ano_rescisao = data_projetada.year
        # Início do período no ano civil: 1º de janeiro ou data de admissão (se admitido no mesmo ano)
        inicio_ano = max(date(ano_rescisao, 1, 1), admissao)

        if inicio_ano > data_projetada:
            return 0

        avos = 0
        mes_atual = inicio_ano.month
        while mes_atual <= data_projetada.month:
            # Primeiro dia de contagem no mês
            dia_inicio = inicio_ano.day if mes_atual == inicio_ano.month else 1

            # Último dia de contagem no mês
            if mes_atual == data_projetada.month:
                dia_fim = data_projetada.day
            else:
                _, dia_fim = monthrange(ano_rescisao, mes_atual)

            dias_trabalhados = (dia_fim - dia_inicio) + 1
            if dias_trabalhados >= 15:
                avos += 1

            mes_atual += 1

        return min(12, avos)

    @staticmethod
    def calcular_avos_ferias_proporcionais(admissao: date, data_projetada: date) -> int:
        """
        Calcula os avos proporcionais (1/12) de férias no período aquisitivo incompleto em curso.
        
        Fundamento Legal:
        - Arts. 130, 146 e 147 da CLT c/c Súmula 171 do TST.
        - Período Aquisitivo: Contado em ciclos de 12 meses a partir do aniversário da admissão.
        - Art. 146, parágrafo único: A fração igual ou superior a 15 dias garante 1/12 avos.
        - O teto máximo de avos proporcionais é 12/12.
        """
        # Localiza o último aniversário da admissão antes da data projetada
        ano_aniversario = data_projetada.year
        try:
            ultimo_aniversario = date(ano_aniversario, admissao.month, admissao.day)
        except ValueError:
            # Trata ano bissexto para admissões em 29 de fevereiro
            ultimo_aniversario = date(ano_aniversario, admissao.month, 28)

        if ultimo_aniversario > data_projetada:
            ano_aniversario -= 1
            try:
                ultimo_aniversario = date(ano_aniversario, admissao.month, admissao.day)
            except ValueError:
                ultimo_aniversario = date(ano_aniversario, admissao.month, 28)

        # Não pode ser anterior à data de admissão original
        inicio_ciclo = max(admissao, ultimo_aniversario)

        # Itera mês a mês do ciclo a partir do dia de aniversário
        avos = 0
        ciclo_atual = inicio_ciclo

        while True:
            # Avança aproximadamente 1 mês no ciclo aquisitivo
            proximo_mes = ciclo_atual.month + 1 if ciclo_atual.month < 12 else 1
            proximo_ano = ciclo_atual.year if ciclo_atual.month < 12 else ciclo_atual.year + 1
            dia_alvo = min(admissao.day, monthrange(proximo_ano, proximo_mes)[1])
            proximo_ciclo = date(proximo_ano, proximo_mes, dia_alvo)

            if proximo_ciclo <= data_projetada:
                avos += 1
                ciclo_atual = proximo_ciclo
                if avos == 12:
                    break
            else:
                # Fração residual final do período aquisitivo incompleto
                dias_residuais = (data_projetada - ciclo_atual).days + 1
                if dias_residuais >= 15:
                    avos += 1
                break

        return min(12, avos)

    # -------------------------------------------------------------------------
    # 3. LIQUIDAÇÃO ANALÍTICA DAS VERBAS E ENCARGOS
    # -------------------------------------------------------------------------

    def liquidar(self) -> DemonstrativoRescisao:
        """
        Executa a liquidação contábil completa de proventos, descontos, FGTS e seguro.
        """
        admissao = self.contrato.data_admissao
        demissao = self.contrato.data_demissao
        salario = self.contrato.salario_base
        tipo_rescisao = self.contrato.tipo_rescisao
        tipo_aviso = self.contrato.tipo_aviso_previo

        anos_completos = self.calcular_anos_completos(admissao, demissao)
        tempo_anos, tempo_meses, tempo_dias = self.calcular_duracao_vinculo(admissao, demissao)
        dias_aviso = self.calcular_dias_aviso_previo(anos_completos)
        data_projetada = self.projetar_data_final(dias_aviso)

        avos_13 = self.calcular_avos_decimo_terceiro(admissao, data_projetada)
        avos_ferias = self.calcular_avos_ferias_proporcionais(admissao, data_projetada)

        demonstrativo = DemonstrativoRescisao(
            dados_contrato=self.contrato,
            data_projetada=data_projetada,
            tempo_servico_anos=tempo_anos,
            tempo_servico_meses=tempo_meses,
            tempo_servico_dias=tempo_dias,
            dias_aviso_previo=dias_aviso,
            avos_decimo_terceiro=avos_13,
            avos_ferias_proporcionais=avos_ferias,
        )

        # ---------------------------------------------------------------------
        # PROVENTO 1: SALDO DE SALÁRIO (Art. 64 c/c Art. 457 CLT)
        # ---------------------------------------------------------------------
        # Empregado mensalista tem base fixada em 30 dias.
        # Os dias de saldo referem-se aos dias do mês de demissão até o afastamento.
        dias_no_mes = monthrange(demissao.year, demissao.month)[1]
        dias_saldo = min(30, demissao.day) if demissao.day == dias_no_mes and dias_no_mes == 31 else demissao.day
        valor_diaria = salario / Decimal("30.00")
        saldo_salario = moeda(valor_diaria * Decimal(dias_saldo))

        demonstrativo.rubricas_proventos.append(
            RubricaRescisoria(
                codigo="001",
                descricao="Saldo de Salário",
                tipo="PROVENTO",
                natureza="REMUNERATORIA",
                referencia=f"{dias_saldo} dias",
                base_legal="Art. 64 da CLT",
                valor=saldo_salario,
            )
        )

        # ---------------------------------------------------------------------
        # PROVENTO 2: AVISO PRÉVIO INDENIZADO (Art. 487, § 1º CLT / Lei 12.506/2011)
        # ---------------------------------------------------------------------
        valor_aviso_indenizado = Decimal("0.00")
        if tipo_aviso == TipoAvisoPrevio.INDENIZADO and dias_aviso > 0:
            if tipo_rescisao == TipoRescisao.SEM_JUSTA_CAUSA:
                valor_aviso_indenizado = moeda(valor_diaria * Decimal(dias_aviso))
                demonstrativo.rubricas_proventos.append(
                    RubricaRescisoria(
                        codigo="002",
                        descricao="Aviso Prévio Indenizado",
                        tipo="PROVENTO",
                        natureza="INDENIZATORIA",
                        referencia=f"{dias_aviso} dias",
                        base_legal="Art. 487, § 1º CLT c/c Lei 12.506/2011",
                        valor=valor_aviso_indenizado,
                    )
                )
            elif tipo_rescisao == TipoRescisao.ACORDO_CONSENSUAL:
                # Art. 484-A, I, 'a' da CLT: Pela metade (50%)
                valor_aviso_integral = valor_diaria * Decimal(dias_aviso)
                valor_aviso_indenizado = moeda(valor_aviso_integral * Decimal("0.50"))
                demonstrativo.rubricas_proventos.append(
                    RubricaRescisoria(
                        codigo="002",
                        descricao="Aviso Prévio Indenizado (50% - Acordo Mútuo)",
                        tipo="PROVENTO",
                        natureza="INDENIZATORIA",
                        referencia=f"{dias_aviso} dias (pago 50%)",
                        base_legal="Art. 484-A, I, 'a' da CLT",
                        valor=valor_aviso_indenizado,
                    )
                )
            elif tipo_rescisao == TipoRescisao.CULPA_RECIPROCA:
                # Súmula 14 do TST: Pela metade (50%)
                valor_aviso_integral = valor_diaria * Decimal(dias_aviso)
                valor_aviso_indenizado = moeda(valor_aviso_integral * Decimal("0.50"))
                demonstrativo.rubricas_proventos.append(
                    RubricaRescisoria(
                        codigo="002",
                        descricao="Aviso Prévio Indenizado (50% - Culpa Recíproca)",
                        tipo="PROVENTO",
                        natureza="INDENIZATORIA",
                        referencia=f"{dias_aviso} dias (50%)",
                        base_legal="Art. 484 CLT / Súmula 14 TST",
                        valor=valor_aviso_indenizado,
                    )
                )

        # ---------------------------------------------------------------------
        # PROVENTO 3: 13º SALÁRIO PROPORCIONAL (Lei nº 4.090/1962)
        # ---------------------------------------------------------------------
        valor_13 = Decimal("0.00")
        if tipo_rescisao != TipoRescisao.COM_JUSTA_CAUSA and avos_13 > 0:
            fator_13 = Decimal("0.50") if tipo_rescisao == TipoRescisao.CULPA_RECIPROCA else Decimal("1.00")
            valor_13 = moeda((salario / Decimal("12.00")) * Decimal(avos_13) * fator_13)
            desc_13 = "13º Salário Proporcional"
            if tipo_rescisao == TipoRescisao.CULPA_RECIPROCA:
                desc_13 += " (50% - Súmula 14 TST)"

            demonstrativo.rubricas_proventos.append(
                RubricaRescisoria(
                    codigo="003",
                    descricao=desc_13,
                    tipo="PROVENTO",
                    natureza="REMUNERATORIA",
                    referencia=f"{avos_13}/12 avos",
                    base_legal="Art. 1º, § 1º Lei 4.090/62 c/c Súmula 157 TST",
                    valor=valor_13,
                )
            )

        # ---------------------------------------------------------------------
        # PROVENTO 4: FÉRIAS VENCIDAS + 1/3 CONSTITUCIONAL (Art. 7º, XVII CF/88 c/c Art. 134 CLT)
        # ---------------------------------------------------------------------
        # Devidas em qualquer modalidade de rescisão, inclusive na Justa Causa (Súmula nº 171 TST).
        if self.contrato.ferias_vencidas_periodos > 0:
            qtd_periodos = self.contrato.ferias_vencidas_periodos
            valor_ferias_vencidas = moeda(salario * Decimal(qtd_periodos))
            terco_vencidas = moeda(valor_ferias_vencidas / Decimal("3.00"))

            demonstrativo.rubricas_proventos.append(
                RubricaRescisoria(
                    codigo="004",
                    descricao=f"Férias Vencidas ({qtd_periodos} período{'s' if qtd_periodos > 1 else ''})",
                    tipo="PROVENTO",
                    natureza="INDENIZATORIA",
                    referencia=f"{qtd_periodos} período(s)",
                    base_legal="Art. 134 e 137 CLT c/c Súmula 171 TST",
                    valor=valor_ferias_vencidas,
                )
            )
            demonstrativo.rubricas_proventos.append(
                RubricaRescisoria(
                    codigo="005",
                    descricao="Terço Constitucional de Férias Vencidas",
                    tipo="PROVENTO",
                    natureza="INDENIZATORIA",
                    referencia="1/3 constitucional",
                    base_legal="Art. 7º, XVII da CF/1988",
                    valor=terco_vencidas,
                )
            )

        # ---------------------------------------------------------------------
        # PROVENTO 5: FÉRIAS PROPORCIONAIS + 1/3 CONSTITUCIONAL (Art. 146 CLT)
        # ---------------------------------------------------------------------
        # Na demissão por justa causa, o empregado PERDE as proporcionais (Súmula 171 TST).
        if tipo_rescisao != TipoRescisao.COM_JUSTA_CAUSA and avos_ferias > 0:
            fator_ferias = Decimal("0.50") if tipo_rescisao == TipoRescisao.CULPA_RECIPROCA else Decimal("1.00")
            valor_ferias_prop = moeda((salario / Decimal("12.00")) * Decimal(avos_ferias) * fator_ferias)
            terco_ferias_prop = moeda(valor_ferias_prop / Decimal("3.00"))

            desc_fp = "Férias Proporcionais"
            if tipo_rescisao == TipoRescisao.CULPA_RECIPROCA:
                desc_fp += " (50% - Súmula 14 TST)"

            demonstrativo.rubricas_proventos.append(
                RubricaRescisoria(
                    codigo="006",
                    descricao=desc_fp,
                    tipo="PROVENTO",
                    natureza="INDENIZATORIA",
                    referencia=f"{avos_ferias}/12 avos",
                    base_legal="Art. 146, parágrafo único da CLT c/c Súmula 261 TST",
                    valor=valor_ferias_prop,
                )
            )
            demonstrativo.rubricas_proventos.append(
                RubricaRescisoria(
                    codigo="007",
                    descricao="Terço Constitucional de Férias Proporcionais",
                    tipo="PROVENTO",
                    natureza="INDENIZATORIA",
                    referencia="1/3 constitucional",
                    base_legal="Art. 7º, XVII da CF/1988",
                    valor=terco_ferias_prop,
                )
            )

        # ---------------------------------------------------------------------
        # PROVENTO 6: INDENIZAÇÃO CONTRATO A TERMO (Art. 479 CLT)
        # ---------------------------------------------------------------------
        if tipo_rescisao == TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADOR and self.contrato.dias_restantes_experiencia > 0:
            # Art. 479: Metade da remuneração a que teria direito até o termo final pactuado
            dias_rest = Decimal(self.contrato.dias_restantes_experiencia)
            indenizacao_479 = moeda((valor_diaria * dias_rest) * Decimal("0.50"))
            demonstrativo.rubricas_proventos.append(
                RubricaRescisoria(
                    codigo="008",
                    descricao="Indenização Rescisão Antecipada (Art. 479 CLT)",
                    tipo="PROVENTO",
                    natureza="INDENIZATORIA",
                    referencia=f"{self.contrato.dias_restantes_experiencia} dias restantes (pago 50%)",
                    base_legal="Art. 479 da CLT",
                    valor=indenizacao_479,
                )
            )

        # ---------------------------------------------------------------------
        # DESCONTO 1: AVISO PRÉVIO INDENIZADO PELO EMPREGADO (Art. 487, § 2º CLT)
        # ---------------------------------------------------------------------
        if (
            tipo_rescisao == TipoRescisao.PEDIDO_DEMISSAO
            and tipo_aviso == TipoAvisoPrevio.NAO_CUMPRIDO_PELO_EMPREGADO
        ):
            # No pedido de demissão não cumprido, desconta-se 30 dias de salário base
            desc_aviso = moeda(salario)
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="101",
                    descricao="Aviso Prévio Não Cumprido (Desconto)",
                    tipo="DESCONTO",
                    natureza="INDENIZATORIA",
                    referencia="30 dias",
                    base_legal="Art. 487, § 2º da CLT",
                    valor=desc_aviso,
                )
            )

        # ---------------------------------------------------------------------
        # DESCONTO 2: INDENIZAÇÃO RESCISÃO ANTECIPADA EMPREGADO (Art. 480 CLT)
        # ---------------------------------------------------------------------
        if tipo_rescisao == TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADO and self.contrato.dias_restantes_experiencia > 0:
            # Art. 480: Indenização de prejuízos limitada ao teto do Art. 479 (50% dos dias restantes)
            dias_rest = Decimal(self.contrato.dias_restantes_experiencia)
            desc_480 = moeda((valor_diaria * dias_rest) * Decimal("0.50"))
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="102",
                    descricao="Indenização Prejuízos Rescisão Antecipada (Art. 480 CLT)",
                    tipo="DESCONTO",
                    natureza="INDENIZATORIA",
                    referencia=f"{self.contrato.dias_restantes_experiencia} dias (teto 50%)",
                    base_legal="Art. 480 da CLT",
                    valor=desc_480,
                )
            )

        # ---------------------------------------------------------------------
        # DESCONTOS 3 E 4: INSS (SALDO DE SALÁRIO E 13º SALÁRIO)
        # ---------------------------------------------------------------------
        # 3.1 INSS sobre Saldo de Salário (Folha Mensal Ordinária)
        inss_saldo, alq_inss_saldo, _ = TabelaINSS.calcular_contribuicao(saldo_salario)
        if inss_saldo > Decimal("0.00"):
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="103",
                    descricao="INSS sobre Saldo de Salário",
                    tipo="DESCONTO",
                    natureza="REMUNERATORIA",
                    referencia=f"{alq_inss_saldo}% efetiva",
                    base_legal="Art. 28 da Lei 8.212/91 c/c EC 103/2019",
                    valor=inss_saldo,
                )
            )

        # 3.2 INSS sobre 13º Salário Proporcional (Tributação Autônoma)
        inss_13, alq_inss_13, _ = TabelaINSS.calcular_contribuicao(valor_13)
        if inss_13 > Decimal("0.00"):
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="104",
                    descricao="INSS sobre 13º Salário Rescisório",
                    tipo="DESCONTO",
                    natureza="REMUNERATORIA",
                    referencia=f"{alq_inss_13}% efetiva",
                    base_legal="Art. 7º, § 2º da Lei 8.620/1993",
                    valor=inss_13,
                )
            )

        # ---------------------------------------------------------------------
        # DESCONTOS 5 E 6: IRRF (SALDO DE SALÁRIO E 13º SALÁRIO)
        # ---------------------------------------------------------------------
        # 4.1 IRRF sobre Saldo de Salário
        irrf_saldo, base_irrf_saldo, alq_irrf_saldo, metodo_irrf_saldo = TabelaIRRF.calcular_imposto(
            rendimento_bruto=saldo_salario,
            inss_descontado=inss_saldo,
            numero_dependentes=self.contrato.numero_dependentes,
        )
        if irrf_saldo > Decimal("0.00"):
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="105",
                    descricao="IRRF sobre Saldo de Salário",
                    tipo="DESCONTO",
                    natureza="REMUNERATORIA",
                    referencia=f"{alq_irrf_saldo}% ({metodo_irrf_saldo})",
                    base_legal="Lei nº 14.663/2023 c/c Art. 677 RIR/2018",
                    valor=irrf_saldo,
                )
            )

        # 4.2 IRRF sobre 13º Salário Proporcional (Tributação Exclusiva na Fonte)
        irrf_13, base_irrf_13, alq_irrf_13, metodo_irrf_13 = TabelaIRRF.calcular_imposto(
            rendimento_bruto=valor_13,
            inss_descontado=inss_13,
            numero_dependentes=self.contrato.numero_dependentes,
        )
        if irrf_13 > Decimal("0.00"):
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="106",
                    descricao="IRRF sobre 13º Salário Rescisório",
                    tipo="DESCONTO",
                    natureza="REMUNERATORIA",
                    referencia=f"{alq_irrf_13}% ({metodo_irrf_13})",
                    base_legal="Art. 638 do RIR/2018 (Tributação Exclusiva)",
                    valor=irrf_13,
                )
            )

        # ---------------------------------------------------------------------
        # DEMAIS DESCONTOS CONTRATUAIS / JUDICIAIS
        # ---------------------------------------------------------------------
        # Adiantamentos Salariais / Vales (Art. 462 CLT)
        if self.contrato.adiantamento_salarial > Decimal("0.00"):
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="107",
                    descricao="Adiantamento Salarial / Vales",
                    tipo="DESCONTO",
                    natureza="REMUNERATORIA",
                    referencia="Compensação",
                    base_legal="Art. 462 da CLT",
                    valor=moeda(self.contrato.adiantamento_salarial),
                )
            )

        # Outros Descontos Autorizados
        if self.contrato.outros_descontos > Decimal("0.00"):
            demonstrativo.rubricas_descontos.append(
                RubricaRescisoria(
                    codigo="108",
                    descricao="Outros Descontos Autorizados",
                    tipo="DESCONTO",
                    natureza="DIVERSOS",
                    referencia="Autorizado",
                    base_legal="Art. 462 da CLT / Súmula 342 TST",
                    valor=moeda(self.contrato.outros_descontos),
                )
            )

        # ---------------------------------------------------------------------
        # TOTALIZAÇÃO DOS PROVENTOS E DESCONTOS
        # ---------------------------------------------------------------------
        total_proventos = sum(r.valor for r in demonstrativo.rubricas_proventos)
        total_descontos_parcial = sum(r.valor for r in demonstrativo.rubricas_descontos)

        # Pensão Alimentícia Judicial (incidência sobre líquido apurado ou proventos)
        if self.contrato.pensao_alimenticia_perc > Decimal("0.00"):
            # A jurisprudência padrão aplica o percentual sobre o saldo líquido antes da pensão
            base_pensao = max(Decimal("0.00"), total_proventos - total_descontos_parcial)
            perc_pensao = self.contrato.pensao_alimenticia_perc / Decimal("100.00")
            valor_pensao = moeda(base_pensao * perc_pensao)
            if valor_pensao > Decimal("0.00"):
                demonstrativo.rubricas_descontos.append(
                    RubricaRescisoria(
                        codigo="109",
                        descricao="Pensão Alimentícia Judicial",
                        tipo="DESCONTO",
                        natureza="JUDICIAL",
                        referencia=f"{self.contrato.pensao_alimenticia_perc}%",
                        base_legal="Ordem Judicial / Lei 5.478/1968",
                        valor=valor_pensao,
                    )
                )

        total_descontos = sum(r.valor for r in demonstrativo.rubricas_descontos)
        total_liquido = max(Decimal("0.00"), total_proventos - total_descontos)

        demonstrativo.total_bruto = moeda(total_proventos)
        demonstrativo.total_descontos = moeda(total_descontos)
        demonstrativo.total_liquido = moeda(total_liquido)

        # ---------------------------------------------------------------------
        # 4. FGTS E MULTA RESCISÓRIA (LEI Nº 8.036/1990)
        # ---------------------------------------------------------------------
        demonstrativo.fgts = self._apurar_fgts(saldo_salario, valor_13)

        # ---------------------------------------------------------------------
        # 5. SEGURO-DESEMPREGO (LEI Nº 7.998/1990)
        # ---------------------------------------------------------------------
        demonstrativo.seguro_desemprego = self._avaliar_seguro_desemprego(tempo_anos, tempo_meses)

        # ---------------------------------------------------------------------
        # 6. PRAZO LEGAL DE PAGAMENTO (Art. 477, § 6º CLT)
        # ---------------------------------------------------------------------
        # Redação da Lei 13.467/2017 unificou o prazo em até 10 dias corridos do término.
        data_limite_pagamento = demissao + timedelta(days=10)
        demonstrativo.prazo_pagamento = (
            f"Até 10 dias corridos ({data_limite_pagamento.strftime('%d/%m/%Y')}) - Art. 477, § 6º da CLT."
        )

        return demonstrativo

    def _apurar_fgts(self, saldo_salario: Decimal, decimo_terceiro: Decimal) -> ResumoFGTS:
        """
        Apura os recolhimentos de FGTS da rescisão, multa indenizatória e regras de saque.
        
        Fundamento Legal:
        - Art. 15 da Lei nº 8.036/1990: Alíquota regular de 8% sobre a remuneração mensal e 13º.
        - Art. 18, § 1º da Lei nº 8.036/1990: Multa rescisória de 40% na demissão sem justa causa.
        - Art. 484-A, § 1º, II da CLT: Multa de 20% no acordo mútuo consensual.
        - Art. 484-A, § 2º da CLT: Movimentação da conta vinculada limitada a até 80% do saldo no acordo.
        """
        tipo_rescisao = self.contrato.tipo_rescisao
        saldo_anterior = self.contrato.saldo_fgts

        # 8% sobre verbas de natureza remuneratória da rescisão
        fgts_rescisorio = moeda((saldo_salario + decimo_terceiro) * Decimal("0.08"))
        base_multa = saldo_anterior + fgts_rescisorio

        if tipo_rescisao in (
            TipoRescisao.SEM_JUSTA_CAUSA,
            TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADOR,
        ):
            perc_multa = Decimal("40.00")
            valor_multa = moeda(base_multa * Decimal("0.40"))
            direito_saque = True
            perc_saque = Decimal("100.00")
            codigo_saque = "Código 01 (Demissão sem justa causa)"
        elif tipo_rescisao == TipoRescisao.ACORDO_CONSENSUAL:
            perc_multa = Decimal("20.00")
            valor_multa = moeda(base_multa * Decimal("0.20"))
            direito_saque = True
            perc_saque = Decimal("80.00")  # Art. 484-A, § 2º CLT
            codigo_saque = "Código 01-A (Acordo Mútuo Art. 484-A CLT - Saque até 80%)"
        elif tipo_rescisao == TipoRescisao.CULPA_RECIPROCA:
            perc_multa = Decimal("20.00")
            valor_multa = moeda(base_multa * Decimal("0.20"))
            direito_saque = True
            perc_saque = Decimal("100.00")
            codigo_saque = "Código 02 (Culpa Recíproca / Força Maior)"
        elif tipo_rescisao == TipoRescisao.TERMINO_CONTRATO_EXPERIENCIA:
            perc_multa = Decimal("0.00")
            valor_multa = Decimal("0.00")
            direito_saque = True
            perc_saque = Decimal("100.00")
            codigo_saque = "Código 04 (Extinção normal de contrato a termo)"
        else:
            # PEDIDO DE DEMISSÃO ou COM JUSTA CAUSA
            perc_multa = Decimal("0.00")
            valor_multa = Decimal("0.00")
            direito_saque = False
            perc_saque = Decimal("0.00")
            codigo_saque = "Sem direito a saque (Saldo retido na Caixa Econômica Federal)"

        total_conta = base_multa + valor_multa
        valor_autorizado = (
            moeda((base_multa * (perc_saque / Decimal("100.00"))) + valor_multa)
            if direito_saque
            else Decimal("0.00")
        )

        return ResumoFGTS(
            saldo_anterior=moeda(saldo_anterior),
            fgts_recolhimento_rescisorio=fgts_rescisorio,
            base_calculo_multa=moeda(base_multa),
            percentual_multa=perc_multa,
            valor_multa=valor_multa,
            total_conta_vinculada=moeda(total_conta),
            percentual_saque=perc_saque,
            valor_autorizado_saque=valor_autorizado,
            direito_saque=direito_saque,
            codigo_saque=codigo_saque,
        )

    def _avaliar_seguro_desemprego(self, anos: int, meses: int) -> ResumoSeguroDesemprego:
        """
        Emite o parecer sobre a habilitação ao benefício do Seguro-Desemprego.
        
        Fundamento Legal:
        - Art. 3º da Lei nº 7.998/1990, alterado pela Lei nº 13.134/2015.
        - Não é devido no Pedido de Demissão, Justa Causa ou Acordo Mútuo (Art. 484-A, § 2º CLT).
        """
        tipo = self.contrato.tipo_rescisao
        meses_totais = (anos * 12) + meses

        if tipo in (TipoRescisao.SEM_JUSTA_CAUSA, TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADOR):
            # Carência legal para primeira solicitação: pelo menos 12 meses de vínculo
            if meses_totais >= 12:
                return ResumoSeguroDesemprego(
                    tem_direito=True,
                    motivo="Habilitado. Vínculo superior a 12 meses preenche os requisitos da Lei 13.134/2015.",
                    meses_trabalhados=meses_totais,
                )
            elif meses_totais >= 6:
                return ResumoSeguroDesemprego(
                    tem_direito=True,
                    motivo="Habilitado condicionalmente (apto se for 2ª ou 3ª solicitação do trabalhador).",
                    meses_trabalhados=meses_totais,
                )
            else:
                return ResumoSeguroDesemprego(
                    tem_direito=False,
                    motivo="Inabilitado por tempo insuficiente (menos de 6 meses de registro).",
                    meses_trabalhados=meses_totais,
                )
        elif tipo == TipoRescisao.ACORDO_CONSENSUAL:
            return ResumoSeguroDesemprego(
                tem_direito=False,
                motivo="Vedação expressa: Rescisão consensual (Art. 484-A, § 2º da CLT) não autoriza seguro-desemprego.",
                meses_trabalhados=meses_totais,
            )
        elif tipo == TipoRescisao.PEDIDO_DEMISSAO:
            return ResumoSeguroDesemprego(
                tem_direito=False,
                motivo="Incompatível: Iniciativa do empregado (pedido de demissão) não enseja proteção contra desemprego involuntário.",
                meses_trabalhados=meses_totais,
            )
        elif tipo == TipoRescisao.COM_JUSTA_CAUSA:
            return ResumoSeguroDesemprego(
                tem_direito=False,
                motivo="Incompatível: Demissão motivada por falta grave (Art. 482 CLT) obsta o benefício.",
                meses_trabalhados=meses_totais,
            )
        else:
            return ResumoSeguroDesemprego(
                tem_direito=False,
                motivo="Não aplicável a esta modalidade rescisória.",
                meses_trabalhados=meses_totais,
            )
