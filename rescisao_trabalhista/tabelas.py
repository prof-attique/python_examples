"""
Módulo de Tabelas Tributárias e Previdenciárias Oficiais.

Implementa o cálculo progressivo de INSS (Previdência Social) segundo a
Emenda Constitucional nº 103/2019 e o cálculo do IRRF (Imposto de Renda Retido
na Fonte) conforme a Lei nº 14.663/2023 e o Regulamento do IR (Decreto 9.580/2018).

Aspectos Técnicos Fundamentais:
1. Precisão Aritmética: Utiliza 'decimal.Decimal' com arredondamento ROUND_HALF_UP
   para evitar discrepâncias de arredondamento de ponto flutuante binário (IEEE 754),
   garantindo estrita conformidade com as regras do eSocial e da Receita Federal do Brasil.
2. Tributação Exclusiva na Fonte: O 13º salário é tributado em separado da remuneração
   mensal (saldo de salário), consoante o Art. 7º, § 2º da Lei nº 8.620/1993 e Art. 638 do RIR/2018.
3. Não Incidências Legais:
   - Aviso Prévio Indenizado: Isento de INSS (Tema 478 STJ - REsp 1.230.957/RS)
     e isento de IRRF (Súmula 215 STJ e Instrução Normativa RFB).
   - Férias Indenizadas + 1/3: Isentas de INSS (Súmula 386 STJ) e de IRRF (Súmulas 125 e 386 STJ).
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple


# Constante de arredondamento monetário de 2 casas decimais (BRL centavos)
CENTAVO = Decimal("0.01")


def moeda(valor: Decimal) -> Decimal:
    """Arredonda estritamente para 2 casas decimais no padrão financeiro brasileiro."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class FaixaProgressiva:
    """Representa um intervalo de incidência tributária com alíquota marginal."""
    limite_inferior: Decimal
    limite_superior: Decimal
    aliquota: Decimal  # Exemplo: Decimal("0.075") para 7.5%


class TabelaINSS:
    """
    Tabela Progressiva de Contribuição Previdenciária dos Segurados Empregados.
    
    Fundamento Legal:
    - Art. 28, § 1º da Lei nº 8.212/1991, com redação dada pela EC nº 103/2019.
    - Portaria Interministerial MPS/MF que estabelece as faixas e o teto previdenciário.
    """

    # Faixas progressivas vigentes (Valores de referência oficiais)
    # Faixa 1: até R$ 1.412,00 -> 7,5%
    # Faixa 2: R$ 1.412,01 até R$ 2.666,68 -> 9,0%
    # Faixa 3: R$ 2.666,69 até R$ 4.000,03 -> 12,0%
    # Faixa 4: R$ 4.000,04 até R$ 7.786,02 -> 14,0%
    # Teto máximo do salário de contribuição: R$ 7.786,02 (máx recolhimento = R$ 908,86)
    FAIXAS: List[FaixaProgressiva] = [
        FaixaProgressiva(Decimal("0.00"), Decimal("1412.00"), Decimal("0.075")),
        FaixaProgressiva(Decimal("1412.00"), Decimal("2666.68"), Decimal("0.090")),
        FaixaProgressiva(Decimal("2666.68"), Decimal("4000.03"), Decimal("0.120")),
        FaixaProgressiva(Decimal("4000.03"), Decimal("7786.02"), Decimal("0.140")),
    ]
    TETO_SALARIAL: Decimal = Decimal("7786.02")

    @classmethod
    def calcular_contribuicao(cls, base_tributavel: Decimal) -> Tuple[Decimal, Decimal, List[Tuple[int, Decimal, Decimal]]]:
        """
        Calcula o desconto de INSS aplicando o fatiamento progressivo por faixas marginais.
        
        Parâmetros:
            base_tributavel: Base remuneratória (Saldo de salário ou 13º salário).
            
        Retorna:
            Uma tupla contendo:
            1. Valor total do recolhimento (Decimal arredondado).
            2. Alíquota efetiva apurada (Decimal, percentual real sobre a base).
            3. Memória descritiva de cálculo por faixa [(faixa_idx, base_na_faixa, imposto_faixa)].
        """
        if base_tributavel <= Decimal("0.00"):
            return Decimal("0.00"), Decimal("0.00"), []

        # O salário de contribuição é limitado ao teto máximo da Previdência Social
        base_aplicavel = min(base_tributavel, cls.TETO_SALARIAL)
        imposto_total = Decimal("0.00")
        memoria: List[Tuple[int, Decimal, Decimal]] = []

        for idx, faixa in enumerate(cls.FAIXAS, start=1):
            if base_aplicavel <= faixa.limite_inferior:
                # A base não atinge esta faixa marginal subsequente
                break

            # Determina a porção da base contida estritamente dentro desta faixa
            topo_faixa = min(base_aplicavel, faixa.limite_superior)
            base_na_faixa = topo_faixa - faixa.limite_inferior

            imposto_faixa = moeda(base_na_faixa * faixa.aliquota)
            imposto_total += imposto_faixa
            memoria.append((idx, base_na_faixa, imposto_faixa))

        imposto_total = moeda(imposto_total)
        aliquota_efetiva = moeda((imposto_total / base_tributavel) * Decimal("100")) if base_tributavel > 0 else Decimal("0.00")

        return imposto_total, aliquota_efetiva, memoria


class TabelaIRRF:
    """
    Tabela Progressiva Mensal do Imposto de Renda Retido na Fonte (IRRF).
    
    Fundamento Legal:
    - Art. 677 do Decreto nº 9.580/2018 (RIR/2018).
    - Lei nº 14.663/2023 c/c Medida Provisória nº 1.206/2024.
    - Sistemática do Desconto Simplificado Mensal (Art. 4º, § 2º da Lei nº 9.250/1995).
    """

    # Dedução legal mensal por dependente cadastrado
    DEDUCAO_DEPENDENTE: Decimal = Decimal("189.59")

    # Desconto simplificado mensal opcional alternativo às deduções legais
    # Fixado em 25% da faixa de isenção (2.259,20 * 0.25 = R$ 564,80)
    DESCONTO_SIMPLIFICADO_PADRAO: Decimal = Decimal("564.80")

    # Estrutura: (limite_superior, aliquota, parcela_a_deduzir)
    TABELA_FAIXAS: List[Tuple[Decimal, Decimal, Decimal]] = [
        (Decimal("2259.20"), Decimal("0.00"), Decimal("0.00")),
        (Decimal("2826.65"), Decimal("0.075"), Decimal("169.44")),
        (Decimal("3751.05"), Decimal("0.150"), Decimal("381.44")),
        (Decimal("4664.68"), Decimal("0.225"), Decimal("662.77")),
        (Decimal("Infinity"), Decimal("0.275"), Decimal("896.00")),
    ]

    @classmethod
    def calcular_imposto(
        cls,
        rendimento_bruto: Decimal,
        inss_descontado: Decimal,
        numero_dependentes: int = 0,
        outras_deducoes: Decimal = Decimal("0.00"),
    ) -> Tuple[Decimal, Decimal, Decimal, str]:
        """
        Calcula o IRRF retido na fonte aplicando automaticamente o critério mais
        vantajoso para o contribuinte (Deduções Legais Tradicionais vs Desconto Simplificado).
        
        Parâmetros:
            rendimento_bruto: Base bruta tributável (ex: Saldo de Salário ou 13º).
            inss_descontado: Valor da contribuição previdenciária descontada desta base.
            numero_dependentes: Quantidade de dependentes legais comprovados.
            outras_deducoes: Ex: pensão alimentícia judicial homologada.
            
        Retorna:
            Tupla contendo:
            1. Valor final do IRRF retido (moeda).
            2. Base de cálculo líquida definitiva utilizada.
            3. Alíquota nominal aplicada (em percentual).
            4. Modalidade de cálculo eleita ("Deduções Legais" ou "Desconto Simplificado").
        """
        if rendimento_bruto <= Decimal("0.00"):
            return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), "Isento"

        # 1. Método das Deduções Legais (INSS + Dependentes + Outras)
        deducoes_dependentes = Decimal(numero_dependentes) * cls.DEDUCAO_DEPENDENTE
        total_deducoes_legais = inss_descontado + deducoes_dependentes + outras_deducoes
        base_legal = max(Decimal("0.00"), rendimento_bruto - total_deducoes_legais)

        # 2. Método do Desconto Simplificado Mensal (Art. 4º, § 2º da Lei nº 9.250/1995)
        # O desconto simplificado substitui todas as deduções ordinárias caso seja mais vantajoso.
        base_simplificada = max(Decimal("0.00"), rendimento_bruto - cls.DESCONTO_SIMPLIFICADO_PADRAO)

        # Apuração do imposto em ambos os métodos
        imposto_legal, aliquota_legal = cls._aplicar_tabela(base_legal)
        imposto_simplificado, aliquota_simplificada = cls._aplicar_tabela(base_simplificada)

        # Escolhe a menor retenção tributária em benefício do trabalhador
        if imposto_simplificado < imposto_legal:
            return moeda(imposto_simplificado), moeda(base_simplificada), aliquota_simplificada, "Desconto Simplificado"
        else:
            return moeda(imposto_legal), moeda(base_legal), aliquota_legal, "Deduções Legais"

    @classmethod
    def _aplicar_tabela(cls, base_calculo: Decimal) -> Tuple[Decimal, Decimal]:
        """Aplica a alíquota marginal e subtrai a parcela dedutível da faixa correspondente."""
        for limite, aliquota, deducao in cls.TABELA_FAIXAS:
            if base_calculo <= limite:
                if aliquota == Decimal("0.00"):
                    return Decimal("0.00"), Decimal("0.00")
                imposto = (base_calculo * aliquota) - deducao
                imposto_positivo = max(Decimal("0.00"), imposto)
                return imposto_positivo, aliquota * Decimal("100")

        # Fallback de segurança para última faixa
        _, aliquota, deducao = cls.TABELA_FAIXAS[-1]
        imposto = (base_calculo * aliquota) - deducao
        return max(Decimal("0.00"), imposto), aliquota * Decimal("100")
