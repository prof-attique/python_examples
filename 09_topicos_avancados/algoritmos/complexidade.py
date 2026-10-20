import time

# Simulando uma base de dados de cidades (1 milhão de registros)
cidades_lista = [f"Cidade_{i}" for i in range(1000000)]
cidades_set = set(cidades_lista) # O(1) para buscas

# ----------------------------------------------------
# MEDINDO ALGORITMO 1: Busca Linear - O(n)
# ----------------------------------------------------
# 1. Captura o tempo inicial
inicio_linear = time.perf_counter()

# Executa o algoritmo (procurando o último elemento da lista)
"Cidade_999999" in cidades_lista

# 2. Captura o tempo final
fim_linear = time.perf_counter()

# 3. Calcula a diferença
tempo_linear = fim_linear - inicio_linear
print(f"Tempo da Busca Linear: {tempo_linear:.6f} segundos")

# ----------------------------------------------------
# MEDINDO ALGORITMO 2: Busca em Hash (Set) - O(1)
# ----------------------------------------------------
inicio_hash = time.perf_counter()

# Executa o mesmo algoritmo, mas usando a estrutura de Set
"Cidade_999999" in cidades_set

fim_hash = time.perf_counter()
tempo_hash = fim_hash - inicio_hash

# ----------------------------------------------------
# EXIBINDO OS RESULTADOS
# ----------------------------------------------------
print(f"Tempo da Busca Linear: {tempo_linear:.6f} segundos")
print(f"Tempo da Busca em Hash: {tempo_hash:.6f} segundos")
