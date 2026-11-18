
# Escrita de arquivos

# Dado um arquivo dados.json faça um algoritimo para criar o arquivo e salvar
# os dados da lista dentro dele.

# NOTA: O arquivo dados.json será criado na raiz do projeto

import json # importa biblioteca do json
import os

CAMINHO_DADOS = os.path.join(os.path.dirname(__file__), "dados.json")

dados = [ {"id": 10, "datahora": "2024-03-02T10:23:39", "temperatura": 23.9} ]

with open(CAMINHO_DADOS, "w") as file: # abre o arquivo no modo escrita
    file.write(json.dumps(dados, indent=4)) # escreve no arquivo convertendo dicionário em json

# Leitura de arquivos
# Dado um arquivo dados.json faça um algoritimo para abir e printar na tela seu conteúdo
with open(CAMINHO_DADOS, "r") as file: # abre o arquivo em modo leitura (read)
    read = file.read()
    print(read)

# Manipulando e alterando arquivos
# Faça um algoritimo que leia o arquivo dados.json e acrescente mais um elemento a lista de 
# medições

def ultimo_id(dados: list) -> int:
    """Retorna o maior ID presente na lista de dicionários"""
    return max([d.get("id", 0) for d in dados], default=0)

dados: list = []
reg: dict = {}

with open(CAMINHO_DADOS, "r") as file: # Primeiro abre para leitura
    # Estamos trabalhando com o padrão JSON
    dados = json.loads(file.read()) # abre e converte a string do read() para dicionário
    print(dados, type(dados)) # agora estamos manipulando uma lista de dicionários
    
    from datetime import datetime # biblioteca de manipular datas

    reg: dict = {"id": ultimo_id(dados)+1, "datahora": datetime.now().isoformat(), "temperatura": 22.9}

with open(CAMINHO_DADOS, "w") as file: # vamos abir o arquivo no modo escrita para subitituir todo seu conteúdo
    # agora adiciona o registro aos dados
    dados.append(reg)
    file.write(json.dumps(dados, indent=4, sort_keys=True, default=str)) # salva novamente no arquivo

with open(CAMINHO_DADOS, "r") as file: # abre o arquivo em modo leitura (read)
    read = file.read()
    print(read)



# As operações para esse arquivo estão muito trabalhosas e exige muito retrabalho
# Crie uma função para fazer a leitura do conteúdo do arquivo json e retornar uma lista de
# dicionários
# Crie outra função para adicionar registros ao arquivo de dados.
def readfile(filename: str) -> str:
    """
    filename: nome do arquivo
    return: uma string com o conteúdo do mesmo

    Uso
    file = json.loads(readfile("data.json"))
    """
    with open(filename, 'r') as file:
        return file.read()

def writefile(filename: str, content: str) -> bool:
    """
    filename: nome do arquivo
    content: conteúdo para inserir no arquivo
    return: um bool para sucesso/fracasso da operação

    Uso
    file = writefile("data.json",json.dumps(dict))
    """
    with open(filename, 'w') as file:
        return file.write(content) > 0