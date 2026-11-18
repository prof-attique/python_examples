#!/usr/bin/env python3
"""
Ponto de Entrada do Sistema de Rescisão Trabalhista (CLT).

Este arquivo reside dentro do próprio módulo 'rescisao_trabalhista' para manter
toda a solução encapsulada em uma única pasta.

Formas de Execução:
    1. A partir da pasta do projeto:
       python3 rescisao_trabalhista/rescisao.py

    2. De dentro da pasta rescisao_trabalhista:
       cd rescisao_trabalhista
       python3 rescisao.py

    3. Como módulo Python padrão:
       python3 -m rescisao_trabalhista
"""

import os
import sys
from pathlib import Path

# Configuração dinâmica do sys.path:
# Garante a resolução correta dos imports tanto quando executado de dentro da pasta
# quanto a partir do diretório raiz.
DIRETORIO_ATUAL = Path(__file__).resolve().parent
DIRETORIO_PAI = DIRETORIO_ATUAL.parent

for diretorio in (str(DIRETORIO_PAI), str(DIRETORIO_ATUAL)):
    if diretorio not in sys.path:
        sys.path.insert(0, diretorio)

# Suporte a import tanto com namespace 'rescisao_trabalhista.cli' quanto direto 'cli'
try:
    from rescisao_trabalhista.cli import main
except ImportError:
    from cli import main

if __name__ == "__main__":
    main()
