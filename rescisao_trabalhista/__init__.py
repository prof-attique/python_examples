"""
Pacote de Cálculo de Rescisão Trabalhista (CLT).

Este pacote provê um motor completo de auditoria e cálculo de verbas rescisórias
trabalhistas de acordo com o arcabouço normativo da Consolidação das Leis do
Trabalho (CLT) e jurisprudência unificada do TST e STJ.
"""

from rescisao_trabalhista.enums import TipoRescisao, TipoAvisoPrevio
from rescisao_trabalhista.models import (
    DadosContrato,
    RubricaRescisoria,
    ResumoFGTS,
    ResumoSeguroDesemprego,
    DemonstrativoRescisao,
)
from rescisao_trabalhista.tabelas import TabelaINSS, TabelaIRRF, moeda
from rescisao_trabalhista.calculadora import CalculadoraRescisao
from rescisao_trabalhista.formatador import FormatadorTRCT

__all__ = [
    "TipoRescisao",
    "TipoAvisoPrevio",
    "DadosContrato",
    "RubricaRescisoria",
    "ResumoFGTS",
    "ResumoSeguroDesemprego",
    "DemonstrativoRescisao",
    "TabelaINSS",
    "TabelaIRRF",
    "CalculadoraRescisao",
    "FormatadorTRCT",
    "moeda",
]
