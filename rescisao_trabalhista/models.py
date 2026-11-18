"""
Módulo de Estruturas de Dados e Modelos do Sistema Rescisório.

Define dataclasses imutáveis e estruturas tipadas que representam o contrato
de trabalho, as verbas rescisórias apuradas e o resumo financeiro consolidado
do Termo de Rescisão do Contrato de Trabalho (TRCT).
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

from rescisao_trabalhista.enums import TipoRescisao, TipoAvisoPrevio


@dataclass
class DadosContrato:
    """
    Parâmetros contratuais e fatos geradores submetidos ao cálculo da rescisão.
    """
    salario_base: Decimal
    data_admissao: date
    data_demissao: date
    tipo_rescisao: TipoRescisao
    tipo_aviso_previo: TipoAvisoPrevio
    saldo_fgts: Decimal = Decimal("0.00")
    ferias_vencidas_periodos: int = 0
    numero_dependentes: int = 0
    adiantamento_salarial: Decimal = Decimal("0.00")
    outros_descontos: Decimal = Decimal("0.00")
    pensao_alimenticia_perc: Decimal = Decimal("0.00")  # Em percentual, ex: Decimal("20.00")
    dias_restantes_experiencia: int = 0  # Relevante para Arts. 479 e 480 da CLT


@dataclass
class RubricaRescisoria:
    """
    Representa uma linha individual de crédito (provento) ou débito (desconto) no TRCT.
    """
    codigo: str
    descricao: str
    tipo: str  # "PROVENTO" ou "DESCONTO"
    natureza: str  # "REMUNERATORIA" (incide encargos) ou "INDENIZATORIA" (isenta)
    referencia: str  # Ex: "15 dias", "8/12 avos", "36 dias"
    base_legal: str  # Dispositivo da CLT, Lei Federal ou Súmula do TST
    valor: Decimal


@dataclass
class ResumoFGTS:
    """
    Demonstrativo do Fundo de Garantia do Tempo de Serviço e Multa Rescisória.
    Fundamento: Lei nº 8.036/1990 e Art. 484-A da CLT.
    """
    saldo_anterior: Decimal
    fgts_recolhimento_rescisorio: Decimal  # 8% sobre saldo de salário e 13º rescisórios
    base_calculo_multa: Decimal
    percentual_multa: Decimal  # 40%, 20% ou 0%
    valor_multa: Decimal
    total_conta_vinculada: Decimal
    percentual_saque: Decimal  # 100%, 80% ou 0%
    valor_autorizado_saque: Decimal
    direito_saque: bool
    codigo_saque: str


@dataclass
class ResumoSeguroDesemprego:
    """
    Parecer de elegibilidade ao Programa de Seguro-Desemprego.
    Fundamento: Lei nº 7.998/1990 e Resoluções CODEFAT.
    """
    tem_direito: bool
    motivo: str
    meses_trabalhados: int


@dataclass
class DemonstrativoRescisao:
    """
    Resultado analítico e sintético consolidado da rescisão contratual.
    """
    dados_contrato: DadosContrato
    data_projetada: date
    tempo_servico_anos: int
    tempo_servico_meses: int
    tempo_servico_dias: int
    dias_aviso_previo: int
    avos_decimo_terceiro: int
    avos_ferias_proporcionais: int

    rubricas_proventos: List[RubricaRescisoria] = field(default_factory=list)
    rubricas_descontos: List[RubricaRescisoria] = field(default_factory=list)

    total_bruto: Decimal = Decimal("0.00")
    total_descontos: Decimal = Decimal("0.00")
    total_liquido: Decimal = Decimal("0.00")

    fgts: Optional[ResumoFGTS] = None
    seguro_desemprego: Optional[ResumoSeguroDesemprego] = None
    prazo_pagamento: str = ""
