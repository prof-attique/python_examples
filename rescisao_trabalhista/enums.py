"""
Módulo de Definições e Enumerações Legais (CLT).

Este módulo centraliza os tipos de desligamento trabalhista e modalidades
de aviso prévio admitidos pela Consolidação das Leis do Trabalho (CLT),
pela Lei nº 12.506/2011 e pela jurisprudência pacificada do TST.
"""

from enum import Enum


class TipoRescisao(str, Enum):
    """
    Modalidades jurídicas de rescisão do contrato individual de trabalho.
    
    Cada modalidade acarreta repercussões específicas sobre os direitos
    rescisórios do trabalhador (verbas rescisórias, multas, saques de FGTS
    e habilitação ao benefício do seguro-desemprego).
    """

    # Demissão sem justa causa por iniciativa do empregador (Art. 477 da CLT).
    # Garante aviso prévio proporcional, 13º e férias proporcionais, saque FGTS,
    # multa rescisória de 40% do FGTS e guias de seguro-desemprego.
    SEM_JUSTA_CAUSA = "SEM_JUSTA_CAUSA"

    # Pedido de demissão por iniciativa do empregado (Art. 477 c/c Art. 487 da CLT).
    # Não confere direito a saque do FGTS nem multa de 40%, nem guias de seguro-desemprego.
    # O aviso prévio deve ser trabalhado ou indenizado pelo empregado (descontado).
    PEDIDO_DEMISSAO = "PEDIDO_DEMISSAO"

    # Demissão motivada por falta grave praticada pelo empregado (Art. 482 da CLT).
    # Limita o pagamento ao saldo de salário e férias simples vencidas (Súmula nº 171 do TST).
    # Perda do direito a férias proporcionais, 13º proporcional, aviso e FGTS.
    COM_JUSTA_CAUSA = "COM_JUSTA_CAUSA"

    # Rescisão por acordo mútuo entre empregado e empregador (Art. 484-A da CLT - Lei 13.467/2017).
    # Aviso indenizado pela metade (50%), multa rescisória do FGTS de 20%,
    # saque de até 80% do saldo do FGTS; sem direito a seguro-desemprego.
    ACORDO_CONSENSUAL = "ACORDO_CONSENSUAL"

    # Término normal de contrato a termo / experiência no prazo pactuado (Art. 443 e 445 da CLT).
    # Não há aviso prévio nem multa rescisória de 40%; garante saque do FGTS código 04.
    TERMINO_CONTRATO_EXPERIENCIA = "TERMINO_CONTRATO_EXPERIENCIA"

    # Rescisão antecipada de contrato por prazo determinado pelo empregador (Art. 479 da CLT).
    # Indenização de metade da remuneração a que o empregado teria direito até o término.
    RESCISAO_ANTECIPADA_EMPREGADOR = "RESCISAO_ANTECIPADA_EMPREGADOR"

    # Rescisão antecipada de contrato por prazo determinado pelo empregado (Art. 480 da CLT).
    # Indenização das perdas e danos causadas ao empregador, limitada ao teto do Art. 479.
    RESCISAO_ANTECIPADA_EMPREGADO = "RESCISAO_ANTECIPADA_EMPREGADO"

    # Culpa recíproca reconhecida pela Justiça do Trabalho (Art. 484 da CLT e Súmula 14 do TST).
    # Reduz pela metade o aviso prévio, 13º salário, férias proporcionais e multa do FGTS (20%).
    CULPA_RECIPROCA = "CULPA_RECIPROCA"

    def descricao_legivel(self) -> str:
        """Retorna uma descrição clara para exibição em menus e relatórios."""
        descricoes = {
            self.SEM_JUSTA_CAUSA: "Demissão sem Justa Causa (Empregador)",
            self.PEDIDO_DEMISSAO: "Pedido de Demissão (Empregado)",
            self.COM_JUSTA_CAUSA: "Demissão com Justa Causa (Art. 482 CLT)",
            self.ACORDO_CONSENSUAL: "Demissão por Acordo Mútuo (Art. 484-A CLT)",
            self.TERMINO_CONTRATO_EXPERIENCIA: "Término Contrato de Experiência / Prazo Determinado",
            self.RESCISAO_ANTECIPADA_EMPREGADOR: "Rescisão Antecipada pelo Empregador (Art. 479 CLT)",
            self.RESCISAO_ANTECIPADA_EMPREGADO: "Rescisão Antecipada pelo Empregado (Art. 480 CLT)",
            self.CULPA_RECIPROCA: "Culpa Recíproca (Art. 484 CLT / Súmula 14 TST)",
        }
        return descricoes.get(self, self.value)


class TipoAvisoPrevio(str, Enum):
    """
    Classificação da modalidade de cumprimento e liquidação do aviso prévio.
    
    Regulamentado pelos Arts. 487 e 488 da CLT e pela Lei nº 12.506/2011.
    """

    # Trabalhado: Empregado cumpre os dias de aviso com faculdade de redução
    # de 2 horas diárias ou 7 dias corridos ao final (Art. 488, parágrafo único da CLT).
    TRABALHADO = "TRABALHADO"

    # Indenizado pelo Empregador: Vínculo cessa de imediato com pagamento pecuniário
    # dos dias devidos e projeção ficcional do contrato (Art. 487, § 1º CLT e Súmula 371 TST).
    INDENIZADO = "INDENIZADO"

    # Não cumprido pelo Empregado: No pedido de demissão, o empregado opta por
    # não cumprir o aviso, ensejando desconto de até 30 dias pelo empregador (Art. 487, § 2º CLT).
    NAO_CUMPRIDO_PELO_EMPREGADO = "NAO_CUMPRIDO_PELO_EMPREGADO"

    # Dispensado: No pedido de demissão, o empregador dispensa o empregado de cumprir
    # o aviso sem efetuar o desconto correspondente (Súmula 276 do TST).
    DISPENSADO_PELO_EMPREGADOR = "DISPENSADO_PELO_EMPREGADOR"

    # Não aplicável: Casos de Justa Causa (Art. 482 CLT) ou término normal de contrato a termo.
    NAO_APLICAVEL = "NAO_APLICAVEL"

    def descricao_legivel(self) -> str:
        """Retorna uma descrição clara para exibição em menus e relatórios."""
        descricoes = {
            self.TRABALHADO: "Trabalhado (com redução legal)",
            self.INDENIZADO: "Indenizado pelo Empregador",
            self.NAO_CUMPRIDO_PELO_EMPREGADO: "Não Cumprido pelo Empregado (Descontado)",
            self.DISPENSADO_PELO_EMPREGADOR: "Dispensado pelo Empregador (Sem Desconto)",
            self.NAO_APLICAVEL: "Não Aplicável ao Motivo de Rescisão",
        }
        return descricoes.get(self, self.value)
