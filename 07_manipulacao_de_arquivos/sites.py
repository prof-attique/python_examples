import os

caminho_arquivo = os.path.join(os.path.dirname(__file__), "sites.txt")

sites = (
    'facebook.com'
    ,'instagram.com'
    ,'friv.com'
    ,'whatsapp.com'
    ,'chat.openai.com'
    ,'netflix.com'
    ,'clickjogos.com'
)

with open(caminho_arquivo, 'w') as f:
    for p in sites:
        f.write(f"127.0.0.1\t{p}\n")
        f.write(f"127.0.0.1\twww.{p}\n")

