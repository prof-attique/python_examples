# 🐍 Repositório Didático de Programação em Python

Bem-vindo ao repositório de ensino e aprendizagem de Python. Este projeto foi estruturado pedagogicamente em uma **trilha linear e modular**, facilitando o estudo progressivo desde os fundamentos da linguagem até padrões avançados e projetos integradores.

---

## 🗺️ Trilha de Aprendizagem (Plano Pedagógico)

| Módulo | Tópico Principal | Conteúdos Chave | Diretório |
| :---: | :--- | :--- | :--- |
| **01** | **Fundamentos** | Entrada/Saída (`print`, `input`), variáveis, operadores aritméticos, tipos primitivos | [`01_fundamentos/`](01_fundamentos/) |
| **02** | **Estruturas Condicionais** | `if`, `elif`, `else`, operadores lógicos/relacionais e `match-case` (Python 3.10+) | [`02_estruturas_condicionais/`](02_estruturas_condicionais/) |
| **03** | **Laços de Repetição** | `while`, `for`, `range()`, `enumerate()`, `break`, `continue` e cláusula `else` | [`03_lacos_de_repeticao/`](03_lacos_de_repeticao/) |
| **04** | **Estruturas de Dados** | Strings, Listas (vetores), Tuplas imutáveis, Dicionários (chave/valor) | [`04_estruturas_de_dados/`](04_estruturas_de_dados/) |
| **05** | **Funções e Módulos** | `def`, parâmetros, retorno, recursividade, pacotes e `import` | [`05_funcoes_e_modulos/`](05_funcoes_e_modulos/) |
| **06** | **Tratamento de Erros** | `try`, `except`, `else`, `finally`, `raise` e boas práticas contra quebras | [`06_tratamento_de_erros/`](06_tratamento_de_erros/) |
| **07** | **Manipulação de Arquivos** | Persistência em disco (`open`, contexto `with`), leitura e escrita de `.txt` e `.json` | [`07_manipulacao_de_arquivos/`](07_manipulacao_de_arquivos/) |
| **08** | **Orientação a Objetos (POO)** | Classes, instâncias, atributos (`__init__`), métodos, `self` e herança | [`08_orientacao_a_objetos/`](08_orientacao_a_objetos/) |
| **09** | **Tópicos Avançados** | Programação assíncrona (`asyncio`), algoritmos, matemática discreta e Design Patterns | [`09_topicos_avancados/`](09_topicos_avancados/) |
| **10** | **Projetos e Exercícios** | Mini-projetos integradores (Controle de Despesas, Sistema Bancário / ProjeX) | [`10_projetos_e_exercicios/`](10_projetos_e_exercicios/) |
| **Extras**| **Ferramentas e Bibliotecas** | Web Scraping (Scrapy/Requests), Interfaces (Tkinter/Kivy), RPA/Automação, Blockchain | [`extras_e_ferramentas/`](extras_e_ferramentas/) |

---

## 📂 Detalhamento dos Módulos

### 01. Fundamentos
- Introdução ao interpretador Python e sintaxe elementar.
- Leitura de dados do terminal via `input()` e formatação de saída com `print()` e f-strings.
- Conversão de tipos (`int()`, `float()`, `str()`).
- Exemplos de cálculos geométricos (área) e cinemática (tempo e distância).

### 02. Estruturas Condicionais
- **`if_else/`**: Tomada de decisões com condições simples, aninhadas e compostas (`and`, `or`, `not`).
- **`match_case/`**: Estrutura moderna de casamento de padrões estruturais (Pattern Matching) introduzida no Python 3.10.

### 03. Laços de Repetição
- **`while/`**: Laços condicionais, loops com sentinela, menus interativos e validação de entradas.
- **`for/`**: Iteração sobre sequências, contadores, geradores de tabuada e tabela verdade, controle com `break`, `continue` e bloco `for-else`.

### 04. Estruturas de Dados
- **`01_strings/`**: Fatiamento, imutabilidade, métodos embutidos.
- **`02_listas/`**: Manipulação de coleções mutáveis (`append`, `pop`, `remove`), iteração e filtragem.
- **`03_tuplas/`**: Uso de registros imutáveis e desempacotamento de variáveis.
- **`04_dicionarios/`**: Estruturas chave-valor, listas de dicionários e modelagem básica de dados.

### 05. Funções e Módulos
- **`01_funcoes/`**: Definição de rotinas (`def`), argumentos, valores de retorno, funções utilitárias.
- **`02_recursividade/`**: Casos base, chamadas recursivas (Fibonacci, Fatorial).
- **`03_modulos/`**: Organização do código em múltiplos arquivos, uso de `__init__.py` e modularização de regras de negócio.

### 06. Tratamento de Erros e Exceções
- Como capturar falhas em tempo de execução (`try ... except ValueError, ZeroDivisionError`).
- Garantia de encerramento de conexões/arquivos com `finally`.

### 07. Manipulação de Arquivos
- Leitura e gravação de arquivos de texto simples (`.txt`).
- Serialização e desserialização de formatos estruturados com a biblioteca nativa `json`.

### 08. Orientação a Objetos (POO)
- Modelagem de entidades do mundo real em classes (`modelos.py`).
- Instanciação de objetos, encapsulamento de comportamentos e métodos especiais (`__str__`).

### 09. Tópicos Avançados
- **`algoritmos/`**: Análise de complexidade, medição de eficiência (`timeit`) e paginação.
- **`async/`**: Programação assíncrona e concorrência com `async` / `await`.
- **`matematica_discreta/`**: Análise combinatória e relações reflexivas/ordem parcial.
- **`padroes_de_projeto/`**: Implementação prática de Design Patterns GoF (Factory Method, Adapter).

### 10. Projetos e Exercícios Integradores
- Aplicações completas em terminal que combinam todos os conceitos aprendidos (estruturas de repetição, coleções, funções, persistência de dados).
  - **`exercicio_final/`**: Sistema de relatório estatístico e financeiro com geração aleatória de dados.
  - **`projex/`**: Sistema interativo de gerenciamento de contas bancárias.

---

## 🚀 Como Executar os Exemplos

### 1. Pré-requisitos
- Python 3.10 ou superior instalado.
- Git configurado.

### 2. Configurar o Ambiente Virtual
Recomenda-se criar um ambiente virtual isolado para não misturar dependências:

```bash
# Criar o ambiente virtual
python3 -m venv .venv

# Ativar no Linux / macOS
source .venv/bin/activate

# Ativar no Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Executando um Exemplo
Você pode executar qualquer arquivo navegando até sua respectiva pasta ou passando o caminho a partir da raiz:

```bash
python3 01_fundamentos/helloworld.py
python3 02_estruturas_condicionais/if_else/ifelse_simples.py
python3 10_projetos_e_exercicios/exercicio_final/main.py
```

---

## 📝 Padrão para Exercícios dos Alunos

Para submissão de atividades e boas práticas de código limpo, utilize o modelo de cabeçalho padronizado disponível em:
👉 [`templates/template_aluno.py`](templates/template_aluno.py)
