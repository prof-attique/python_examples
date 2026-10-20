import time

def somador(n):
    soma = 0
    for p in range(1, n + 1):
        soma += p
        print(p,soma)
    return soma

# Marca o tempo inicial
inicio = time.perf_counter()
somador(5)
# Marca o tempo final
fim = time.perf_counter()

# Calcula o tempo de execução
print(f"Tempo de execução: {fim - inicio:.6f} segundos")