"""
Módulo de Formatação e Emissão do Termo de Rescisão do Contrato de Trabalho (TRCT).

Gera visualizações em padrão tabular e terminal com cores ANSI, estruturado
segundo os moldes do Termo de Homologação de Rescisão (Portaria MTE nº 1.057/2012)
e demonstrativos de auditoria trabalhista.
"""

import sys
from decimal import Decimal
from typing import List

from rescisao_trabalhista.models import DemonstrativoRescisao, RubricaRescisoria


class Cores:
    """Códigos de escape ANSI para formatação tipográfica em terminais Unix/Linux."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Cores de Texto
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Cores Claras / Brilhantes
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_WHITE = "\033[97m"

    # Cores de Fundo
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_DARK = "\033[40m"


def formatar_moeda(valor: Decimal) -> str:
    """Formata valor Decimal para string no formato financeiro brasileiro (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class FormatadorTRCT:
    """
    Formatador de relatório de rescisão para saída em terminal.
    """

    def __init__(self, demonstrativo: DemonstrativoRescisao, usar_cores: bool = True):
        self.dem = demonstrativo
        self.usar_cores = usar_cores and sys.stdout.isatty()

    def _c(self, cor: str, texto: str) -> str:
        """Aplica cor ANSI caso a estilização esteja ativada."""
        if self.usar_cores:
            return f"{cor}{texto}{Cores.RESET}"
        return texto

    def gerar_relatorio(self) -> str:
        """Compila o relatório analítico completo da rescisão trabalhista."""
        linhas: List[str] = []
        largura = 96
        linha_fina = "─" * largura

        # ---------------------------------------------------------------------
        # CABEÇALHO DO SISTEMA
        # ---------------------------------------------------------------------
        linhas.append(self._c(Cores.CYAN + Cores.BOLD, "╔" + "═" * (largura - 2) + "╗"))
        titulo = "DEMONSTRATIVO DE RESCISÃO DO CONTRATO DE TRABALHO (CLT / TRCT)"
        subtitulo = "Conformidade com a CLT, Lei 12.506/2011, Lei 8.036/1990 e Jurisprudência TST"
        linhas.append(self._c(Cores.CYAN + Cores.BOLD, f"║{titulo.center(largura - 2)}║"))
        linhas.append(self._c(Cores.DIM, f"║{subtitulo.center(largura - 2)}║"))
        linhas.append(self._c(Cores.CYAN + Cores.BOLD, "╚" + "═" * (largura - 2) + "╝"))
        linhas.append("")

        # ---------------------------------------------------------------------
        # SEÇÃO 1: IDENTIFICAÇÃO CONTRATUAL E CRONOLOGIA
        # ---------------------------------------------------------------------
        linhas.append(self._c(Cores.BLUE + Cores.BOLD, "  1. PARÂMETROS CONTRATUAIS E CRONOLÓGICOS"))
        linhas.append(self._c(Cores.DIM, "  " + linha_fina[: largura - 4]))

        c = self.dem.dados_contrato
        linhas.append(f"  • Salário Base Mensal      : {self._c(Cores.BOLD, formatar_moeda(c.salario_base))}")
        linhas.append(f"  • Data de Admissão         : {c.data_admissao.strftime('%d/%m/%Y')}")
        linhas.append(f"  • Data de Desligamento     : {c.data_demissao.strftime('%d/%m/%Y')}")
        linhas.append(f"  • Data Final Projetada     : {self._c(Cores.BRIGHT_YELLOW, self.dem.data_projetada.strftime('%d/%m/%Y'))} (OJ 82 SDI-1 TST / Súmula 371 TST)")
        linhas.append(
            f"  • Tempo Efetivo de Serviço : {self.dem.tempo_servico_anos} ano(s), "
            f"{self.dem.tempo_servico_meses} mês(es) e {self.dem.tempo_servico_dias} dia(s)"
        )
        linhas.append(f"  • Modalidade de Rescisão   : {self._c(Cores.BOLD, c.tipo_rescisao.descricao_legivel())}")
        linhas.append(
            f"  • Aviso Prévio             : {c.tipo_aviso_previo.descricao_legivel()} "
            f"({self._c(Cores.BRIGHT_YELLOW, str(self.dem.dias_aviso_previo) + ' dias apurados')})"
        )
        linhas.append(
            f"  • Frações Apuradas (Avos)  : 13º Salário: {self._c(Cores.BOLD, str(self.dem.avos_decimo_terceiro) + '/12')} | "
            f"Férias Proporcionais: {self._c(Cores.BOLD, str(self.dem.avos_ferias_proporcionais) + '/12')}"
        )
        if c.ferias_vencidas_periodos > 0:
            linhas.append(f"  • Férias Vencidas Integrais: {c.ferias_vencidas_periodos} período(s) aquisitivo(s) pendente(s)")
        if c.numero_dependentes > 0:
            linhas.append(f"  • Dependentes para IRRF    : {c.numero_dependentes} dependente(s) legal(is)")
        linhas.append("")

        # ---------------------------------------------------------------------
        # SEÇÃO 2: PROVENTOS (VERBAS RESCISÓRIAS BRUTAS)
        # ---------------------------------------------------------------------
        col_cod = 5
        col_desc = 36
        col_ref = 13
        col_base = 18
        col_val = 13

        linhas.append(self._c(Cores.GREEN + Cores.BOLD, "  2. VERBAS RESCISÓRIAS A FAVOR DO TRABALHADOR (PROVENTOS)"))
        linhas.append("  ┌" + "─" * (col_cod + 2) + "┬" + "─" * (col_desc + 2) + "┬" + "─" * (col_ref + 2) + "┬" + "─" * (col_base + 2) + "┬" + "─" * (col_val + 2) + "┐")
        linhas.append(
            f"  │ {'CÓD':<{col_cod}} │ {'DESCRIÇÃO DA RUBRICA':<{col_desc}} │ {'REFERÊNCIA':<{col_ref}} │ {'BASE LEGAL':<{col_base}} │ {'VALOR (R$)':>{col_val}} │"
        )
        linhas.append("  ├" + "─" * (col_cod + 2) + "┼" + "─" * (col_desc + 2) + "┼" + "─" * (col_ref + 2) + "┼" + "─" * (col_base + 2) + "┼" + "─" * (col_val + 2) + "┤")

        for r in self.dem.rubricas_proventos:
            desc = r.descricao[:col_desc]
            ref = r.referencia[:col_ref]
            base = r.base_legal[:col_base]
            val = formatar_moeda(r.valor).rjust(col_val)
            val_formatado = self._c(Cores.GREEN, val)
            linhas.append(
                f"  │ {r.codigo:<{col_cod}} │ {desc:<{col_desc}} │ {ref:<{col_ref}} │ {base:<{col_base}} │ {val_formatado} │"
            )

        linhas.append("  └" + "─" * (col_cod + 2) + "┴" + "─" * (col_desc + 2) + "┴" + "─" * (col_ref + 2) + "┴" + "─" * (col_base + 2) + "┴" + "─" * (col_val + 2) + "┘")
        total_p_fmt = formatar_moeda(self.dem.total_bruto)
        linhas.append(
            f"  Subtotal de Proventos (Bruto): " + self._c(Cores.BRIGHT_GREEN + Cores.BOLD, total_p_fmt)
        )
        linhas.append("")

        # ---------------------------------------------------------------------
        # SEÇÃO 3: DESCONTOS (ENCARGOS LEGAIS E RETENÇÕES)
        # ---------------------------------------------------------------------
        linhas.append(self._c(Cores.RED + Cores.BOLD, "  3. RETENÇÕES, TRIBUTOS E DESCONTOS (DÉBITOS)"))
        if self.dem.rubricas_descontos:
            linhas.append("  ┌" + "─" * (col_cod + 2) + "┬" + "─" * (col_desc + 2) + "┬" + "─" * (col_ref + 2) + "┬" + "─" * (col_base + 2) + "┬" + "─" * (col_val + 2) + "┐")
            linhas.append(
                f"  │ {'CÓD':<{col_cod}} │ {'DESCRIÇÃO DO DESCONTO':<{col_desc}} │ {'REFERÊNCIA':<{col_ref}} │ {'BASE LEGAL':<{col_base}} │ {'VALOR (R$)':>{col_val}} │"
            )
            linhas.append("  ├" + "─" * (col_cod + 2) + "┼" + "─" * (col_desc + 2) + "┼" + "─" * (col_ref + 2) + "┼" + "─" * (col_base + 2) + "┼" + "─" * (col_val + 2) + "┤")

            for r in self.dem.rubricas_descontos:
                desc = r.descricao[:col_desc]
                ref = r.referencia[:col_ref]
                base = r.base_legal[:col_base]
                val = formatar_moeda(r.valor).rjust(col_val)
                val_formatado = self._c(Cores.RED, val)
                linhas.append(
                    f"  │ {r.codigo:<{col_cod}} │ {desc:<{col_desc}} │ {ref:<{col_ref}} │ {base:<{col_base}} │ {val_formatado} │"
                )

            linhas.append("  └" + "─" * (col_cod + 2) + "┴" + "─" * (col_desc + 2) + "┴" + "─" * (col_ref + 2) + "┴" + "─" * (col_base + 2) + "┴" + "─" * (col_val + 2) + "┘")
            total_d_fmt = formatar_moeda(self.dem.total_descontos)
            linhas.append(
                f"  Subtotal de Descontos: " + self._c(Cores.BRIGHT_RED + Cores.BOLD, total_d_fmt)
            )
        else:
            linhas.append(self._c(Cores.DIM, "  (Nenhum desconto legal ou contratual incidente)"))
        linhas.append("")

        # ---------------------------------------------------------------------
        # SEÇÃO 4: RESUMO SINTÉTICO (TOTALIZAÇÃO LÍQUIDA)
        # ---------------------------------------------------------------------
        largura_quadro = 88
        linhas.append(self._c(Cores.YELLOW + Cores.BOLD, "  4. QUADRO DE FECHAMENTO FINANCEIRO"))
        linhas.append("  ┌" + "─" * largura_quadro + "┐")
        p_txt = f"Total Bruto de Proventos   : {formatar_moeda(self.dem.total_bruto):>18}"
        d_txt = f"Total Geral de Descontos   : {formatar_moeda(self.dem.total_descontos):>18}"
        liq_txt = f"VALOR LÍQUIDO A RECEBER    : {formatar_moeda(self.dem.total_liquido):>18}"

        linhas.append(f"  │  (+) {self._c(Cores.GREEN, p_txt):<98}│")
        linhas.append(f"  │  (-) {self._c(Cores.RED, d_txt):<98}│")
        linhas.append("  │  " + "─" * (largura_quadro - 4) + "  │")
        linhas.append(f"  │  (=) {self._c(Cores.BRIGHT_YELLOW + Cores.BOLD, liq_txt):<98}│")
        linhas.append("  └" + "─" * largura_quadro + "┘")
        linhas.append("")

        # ---------------------------------------------------------------------
        # SEÇÃO 5: FGTS E MULTA RESCISÓRIA (LEI Nº 8.036/1990)
        # ---------------------------------------------------------------------
        if self.dem.fgts:
            fg = self.dem.fgts
            linhas.append(self._c(Cores.CYAN + Cores.BOLD, "  5. DEMONSTRATIVO DO FGTS E MULTA INDENIZATÓRIA (LEI 8.036/90)"))
            linhas.append(self._c(Cores.DIM, "  " + linha_fina[: largura - 4]))
            linhas.append(f"  • Saldo Anterior da Conta Vinculada : {formatar_moeda(fg.saldo_anterior)}")
            linhas.append(
                f"  • FGTS Rescisório sobre a Folha (8%): {formatar_moeda(fg.fgts_recolhimento_rescisorio)} "
                f"(recolhido via GRRF/FGTS Digital sobre saldo e 13º)"
            )
            linhas.append(f"  • Base de Cálculo da Multa FGTS    : {formatar_moeda(fg.base_calculo_multa)}")
            linhas.append(
                f"  • Multa Rescisória Indenizatória   : {self._c(Cores.BRIGHT_GREEN if fg.valor_multa > 0 else Cores.DIM, formatar_moeda(fg.valor_multa))} "
                f"({fg.percentual_multa:.0f}% sobre base rescisória)"
            )
            linhas.append(f"  • Saldo Global da Conta Vinculada  : {formatar_moeda(fg.total_conta_vinculada)}")
            saque_status = (
                self._c(Cores.BRIGHT_GREEN + Cores.BOLD, f"LIBERADO ({fg.codigo_saque})")
                if fg.direito_saque
                else self._c(Cores.RED + Cores.BOLD, "RETIDO (Sem direito a levantamento imediato)")
            )
            linhas.append(f"  • Situação do Saque do FGTS        : {saque_status}")
            if fg.direito_saque:
                linhas.append(
                    f"  • Valor Estimado Autorizado Saque  : {self._c(Cores.BRIGHT_GREEN + Cores.BOLD, formatar_moeda(fg.valor_autorizado_saque))} "
                    f"({fg.percentual_saque:.0f}% da conta + multa)"
                )
            linhas.append("")

        # ---------------------------------------------------------------------
        # SEÇÃO 6: DIREITOS ACESSÓRIOS E OBSERVAÇÕES LEGAIS
        # ---------------------------------------------------------------------
        linhas.append(self._c(Cores.MAGENTA + Cores.BOLD, "  6. DIREITOS COMPLEMENTARES E PRAZOS PROCESSUAIS"))
        linhas.append(self._c(Cores.DIM, "  " + linha_fina[: largura - 4]))

        if self.dem.seguro_desemprego:
            sd = self.dem.seguro_desemprego
            status_sd = (
                self._c(Cores.BRIGHT_GREEN + Cores.BOLD, "HABILITADO")
                if sd.tem_direito
                else self._c(Cores.RED + Cores.BOLD, "INABILITADO")
            )
            linhas.append(f"  • Seguro-Desemprego (Lei 7.998/90) : {status_sd}")
            linhas.append(f"    Parecer Técnico                  : {sd.motivo}")

        linhas.append(f"  • Prazo para Liquidação e Quitação : {self._c(Cores.BRIGHT_WHITE, self.dem.prazo_pagamento)}")
        linhas.append(f"  • Sanção por Inadimplemento        : Multa de 1 salário contratual em favor do trabalhador (Art. 477, § 8º da CLT).")
        linhas.append("")

        return "\n".join(linhas)
