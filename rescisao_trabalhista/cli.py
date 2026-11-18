"""
Módulo de Interface de Linha de Comando (CLI) para Rescisão Trabalhista.

Oferece suporte a:
1. Modo Interativo: Assistente guiado em terminal com validações estritas de tipos,
   formatação brasileira e lógica adaptativa aos motivos de desligamento.
2. Modo Automatizado (Batch / Flags): Processamento via argumentos de linha de comando
   (argparse) para scripts de automação, CI/CD ou integração com eSocial.
"""

import argparse
import sys
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional

from rescisao_trabalhista.enums import TipoRescisao, TipoAvisoPrevio
from rescisao_trabalhista.models import DadosContrato
from rescisao_trabalhista.calculadora import CalculadoraRescisao
from rescisao_trabalhista.formatador import FormatadorTRCT, Cores


def parse_data(texto: str) -> date:
    """
    Converte string em formato de data (DD/MM/AAAA ou AAAA-MM-DD).
    
    Lança ValueError caso o formato seja inválido ou o dia seja inexistente no calendário.
    """
    texto = texto.strip()
    formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Data inválida '{texto}'. Utilize o formato DD/MM/AAAA.")


def parse_decimal(texto: str, default: Decimal = Decimal("0.00")) -> Decimal:
    """
    Converte entrada monetária em Decimal, aceitando formatos com vírgula ou ponto.
    Exemplos: '3.500,50' -> 3500.50, '3500.50' -> 3500.50, '3500' -> 3500.00.
    """
    texto = texto.strip()
    if not texto:
        return default

    # Remove símbolos de moeda caso existam
    texto = texto.replace("R$", "").replace("r$", "").strip()

    # Trata separadores de milhar e decimal do padrão pt-BR
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        val = Decimal(texto)
        if val < Decimal("0.00"):
            raise ValueError("O valor não pode ser negativo.")
        return val
    except (InvalidOperation, ValueError) as err:
        raise ValueError(f"Valor monetário inválido: '{texto}'.") from err


def solicitar_input(prompt: str, validador, valor_padrao=None, ajuda: str = ""):
    """Loop de leitura com validação e mensagens de erro no terminal."""
    while True:
        try:
            sufixo_padrao = f" [{valor_padrao}]" if valor_padrao is not None else ""
            dica_ajuda = f" ({ajuda})" if ajuda else ""
            entrada = input(f"{Cores.BOLD}{prompt}{dica_ajuda}{sufixo_padrao}:{Cores.RESET} ").strip()

            if not entrada and valor_padrao is not None:
                return valor_padrao

            return validador(entrada)
        except Exception as e:
            print(f"{Cores.RED}  [!] Erro: {e}{Cores.RESET}")


def menu_interativo() -> DadosContrato:
    """
    Executa o questionário guiado de dados contratuais no terminal.
    """
    print(f"\n{Cores.CYAN}{Cores.BOLD}{'═' * 70}")
    print("  ASSISTENTE INTERATIVO DE CÁLCULO DE RESCISÃO TRABALHISTA (CLT)")
    print(f"{'═' * 70}{Cores.RESET}\n")

    # 1. Salário Base Contratual
    salario = solicitar_input(
        "Salário Bruto Contratual (R$)",
        lambda s: parse_decimal(s),
        ajuda="ex: 4500,00",
    )

    # 2. Datas de Admissão e Afastamento
    while True:
        admissao = solicitar_input(
            "Data de Admissão",
            parse_data,
            ajuda="DD/MM/AAAA",
        )
        demissao = solicitar_input(
            "Data de Desligamento / Afastamento",
            parse_data,
            ajuda="DD/MM/AAAA",
        )
        if demissao >= admissao:
            break
        print(f"{Cores.RED}  [!] A data de desligamento deve ser igual ou posterior à data de admissão!{Cores.RESET}")

    # 3. Motivo da Rescisão Contratual
    print(f"\n{Cores.BLUE}{Cores.BOLD}Selecione a Modalidade de Rescisão Contratual:{Cores.RESET}")
    opcoes_rescisao = [
        (TipoRescisao.SEM_JUSTA_CAUSA, "Demissão sem Justa Causa (Iniciativa do Empregador)"),
        (TipoRescisao.PEDIDO_DEMISSAO, "Pedido de Demissão (Iniciativa do Empregado)"),
        (TipoRescisao.COM_JUSTA_CAUSA, "Demissão por Justa Causa (Art. 482 CLT - Falta Grave)"),
        (TipoRescisao.ACORDO_CONSENSUAL, "Demissão por Acordo Mútuo (Art. 484-A CLT - Reforma Trabalhista)"),
        (TipoRescisao.TERMINO_CONTRATO_EXPERIENCIA, "Término Contrato de Experiência / Prazo Determinado"),
        (TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADOR, "Rescisão Antecipada de Experiência pelo Empregador (Art. 479 CLT)"),
        (TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADO, "Rescisão Antecipada de Experiência pelo Empregado (Art. 480 CLT)"),
        (TipoRescisao.CULPA_RECIPROCA, "Culpa Recíproca Judicialmente Reconhecida (Art. 484 CLT)"),
    ]

    for idx, (_, rotulo) in enumerate(opcoes_rescisao, start=1):
        print(f"  [{idx}] {rotulo}")

    escolha_rescisao = solicitar_input(
        "Opção desejada",
        lambda x: int(x) if 1 <= int(x) <= len(opcoes_rescisao) else (_ for _ in ()).throw(ValueError("Opção inexistente")),
        valor_padrao=1,
    )
    tipo_rescisao = opcoes_rescisao[escolha_rescisao - 1][0]

    # 4. Modalidade de Aviso Prévio (Condicional ao motivo da rescisão)
    tipo_aviso = TipoAvisoPrevio.NAO_APLICAVEL
    dias_restantes_experiencia = 0

    if tipo_rescisao in (TipoRescisao.SEM_JUSTA_CAUSA, TipoRescisao.ACORDO_CONSENSUAL, TipoRescisao.CULPA_RECIPROCA):
        print(f"\n{Cores.BLUE}{Cores.BOLD}Modalidade de Cumprimento do Aviso Prévio:{Cores.RESET}")
        print("  [1] Indenizado pelo Empregador (Desligamento Imediato c/ Projeção)")
        print("  [2] Trabalhado pelo Empregado (Cumprimento Integral / Redução Legal)")
        escolha_av = solicitar_input(
            "Opção de Aviso",
            lambda x: int(x) if x in ("1", "2") else (_ for _ in ()).throw(ValueError("Escolha 1 ou 2")),
            valor_padrao=1,
        )
        tipo_aviso = TipoAvisoPrevio.INDENIZADO if escolha_av == 1 else TipoAvisoPrevio.TRABALHADO

    elif tipo_rescisao == TipoRescisao.PEDIDO_DEMISSAO:
        print(f"\n{Cores.BLUE}{Cores.BOLD}Cumprimento do Aviso Prévio pelo Trabalhador:{Cores.RESET}")
        print("  [1] Trabalhado (Cumprido integralmente)")
        print("  [2] Não Cumprido (Desconto de 30 dias de salário pelo empregador)")
        print("  [3] Dispensado pelo Empregador (Livre de desconto, Súmula 276 TST)")
        escolha_av = solicitar_input(
            "Opção de Aviso",
            lambda x: int(x) if x in ("1", "2", "3") else (_ for _ in ()).throw(ValueError("Escolha 1, 2 ou 3")),
            valor_padrao=1,
        )
        mapa_av = {
            1: TipoAvisoPrevio.TRABALHADO,
            2: TipoAvisoPrevio.NAO_CUMPRIDO_PELO_EMPREGADO,
            3: TipoAvisoPrevio.DISPENSADO_PELO_EMPREGADOR,
        }
        tipo_aviso = mapa_av[escolha_av]

    elif tipo_rescisao in (TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADOR, TipoRescisao.RESCISAO_ANTECIPADA_EMPREGADO):
        dias_restantes_experiencia = solicitar_input(
            "Quantos dias faltavam para o término pactuado do contrato a termo?",
            lambda x: int(x) if int(x) >= 0 else (_ for _ in ()).throw(ValueError("Dias deve ser >= 0")),
            valor_padrao=30,
        )

    # 5. Saldo da Conta Vinculada do FGTS
    saldo_fgts = solicitar_input(
        "\nSaldo Atual para Fins Rescisórios do FGTS (Extrato CEF)",
        lambda s: parse_decimal(s),
        valor_padrao=Decimal("0.00"),
        ajuda="deixe 0 se não souber",
    )

    # 6. Férias Vencidas Integrais Pendentes de Gozo
    ferias_vencidas = solicitar_input(
        "Quantidade de Períodos Aquisitivos de Férias VENCIDAS (não gozadas)",
        lambda x: int(x) if int(x) >= 0 else (_ for _ in ()).throw(ValueError("Períodos deve ser >= 0")),
        valor_padrao=0,
        ajuda="0 para nenhuma, 1 para 1 ano vencido, etc.",
    )

    # 7. Deduções Legais do IRRF (Dependentes)
    dependentes = solicitar_input(
        "Número de Dependentes Legais (para dedução do Imposto de Renda)",
        lambda x: int(x) if int(x) >= 0 else (_ for _ in ()).throw(ValueError("Número de dependentes deve ser >= 0")),
        valor_padrao=0,
    )

    # 8. Outros Descontos Contratuais / Adiantamentos
    adiantamento = solicitar_input(
        "Adiantamento Salarial / Vales a compensar (R$)",
        lambda s: parse_decimal(s),
        valor_padrao=Decimal("0.00"),
    )

    outros_descontos = solicitar_input(
        "Outros Descontos Autorizados (ex: coparticipação, farmácia) (R$)",
        lambda s: parse_decimal(s),
        valor_padrao=Decimal("0.00"),
    )

    pensao_perc = solicitar_input(
        "Pensão Alimentícia Judicial (%) a reter",
        lambda s: parse_decimal(s),
        valor_padrao=Decimal("0.00"),
        ajuda="0 se não houver",
    )

    return DadosContrato(
        salario_base=salario,
        data_admissao=admissao,
        data_demissao=demissao,
        tipo_rescisao=tipo_rescisao,
        tipo_aviso_previo=tipo_aviso,
        saldo_fgts=saldo_fgts,
        ferias_vencidas_periodos=ferias_vencidas,
        numero_dependentes=dependentes,
        adiantamento_salarial=adiantamento,
        outros_descontos=outros_descontos,
        pensao_alimenticia_perc=pensao_perc,
        dias_restantes_experiencia=dias_restantes_experiencia,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Sistema de Auditoria e Cálculo de Rescisão Trabalhista (CLT / eSocial).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--salario", type=str, help="Salário base mensal (ex: 4500.00)")
    parser.add_argument("--admissao", type=str, help="Data de admissão (DD/MM/AAAA ou AAAA-MM-DD)")
    parser.add_argument("--demissao", type=str, help="Data de demissão (DD/MM/AAAA ou AAAA-MM-DD)")
    parser.add_argument(
        "--motivo",
        type=str,
        choices=[t.value.lower() for t in TipoRescisao],
        help="Modalidade jurídica de rescisão",
    )
    parser.add_argument(
        "--aviso",
        type=str,
        choices=[a.value.lower() for a in TipoAvisoPrevio],
        default="indenizado",
        help="Tipo de aviso prévio",
    )
    parser.add_argument("--fgts", type=str, default="0.00", help="Saldo da conta vinculada do FGTS")
    parser.add_argument("--ferias-vencidas", type=int, default=0, help="Períodos de férias vencidas")
    parser.add_argument("--dependentes", type=int, default=0, help="Quantidade de dependentes para IRRF")
    parser.add_argument("--adiantamento", type=str, default="0.00", help="Adiantamento salarial a descontar")
    parser.add_argument("--outros-descontos", type=str, default="0.00", help="Outros descontos autorizados")
    parser.add_argument("--pensao", type=str, default="0.00", help="Percentual de pensão alimentícia")
    parser.add_argument("--dias-restantes", type=int, default=0, help="Dias restantes para Arts. 479/480 CLT")
    parser.add_argument("--salvar", type=str, help="Caminho de arquivo para salvar o relatório gerado")
    parser.add_argument("--sem-cores", action="store_true", help="Desativa estilizações ANSI de cores")

    return parser


def main():
    """Ponto de entrada executável do sistema de rescisão."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # Se os argumentos essenciais foram fornecidos via CLI, processa direto; senão, entra no modo interativo.
    if args.salario and args.admissao and args.demissao and args.motivo:
        try:
            contrato = DadosContrato(
                salario_base=parse_decimal(args.salario),
                data_admissao=parse_data(args.admissao),
                data_demissao=parse_data(args.demissao),
                tipo_rescisao=TipoRescisao[args.motivo.upper()],
                tipo_aviso_previo=TipoAvisoPrevio[args.aviso.upper()],
                saldo_fgts=parse_decimal(args.fgts),
                ferias_vencidas_periodos=args.ferias_vencidas,
                numero_dependentes=args.dependentes,
                adiantamento_salarial=parse_decimal(args.adiantamento),
                outros_descontos=parse_decimal(args.outros_descontos),
                pensao_alimenticia_perc=parse_decimal(args.pensao),
                dias_restantes_experiencia=args.dias_restantes,
            )
        except Exception as err:
            print(f"{Cores.RED}Erro nos parâmetros de linha de comando: {err}{Cores.RESET}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            contrato = menu_interativo()
        except KeyboardInterrupt:
            print(f"\n{Cores.YELLOW}Operação cancelada pelo usuário.{Cores.RESET}")
            sys.exit(0)

    # Executa a liquidação contábil
    calculadora = CalculadoraRescisao(contrato)
    demonstrativo = calculadora.liquidar()

    # Formata a emissão
    usar_cores = not args.sem_cores
    formatador = FormatadorTRCT(demonstrativo, usar_cores=usar_cores)
    relatorio = formatador.gerar_relatorio()

    print("\n" + relatorio)

    # Opcional: salvar em arquivo
    if args.salvar:
        formatador_puro = FormatadorTRCT(demonstrativo, usar_cores=False)
        with open(args.salvar, "w", encoding="utf-8") as f:
            f.write(formatador_puro.gerar_relatorio())
        print(f"\n{Cores.GREEN}✓ Relatório salvo com sucesso em: {args.salvar}{Cores.RESET}\n")


if __name__ == "__main__":
    main()
