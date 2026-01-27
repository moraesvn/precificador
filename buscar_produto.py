import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ID do produto
PRODUTO_ID = 4464

# Carregar access token
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("[ERRO] TINY_ACCESS_TOKEN nao encontrado no .env")
    exit(1)

ACCESS_TOKEN = ACCESS_TOKEN.strip()

# URL da API
url = f"https://api.tiny.com.br/public-api/v3/produtos/{PRODUTO_ID}"

# Headers
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

print(f"Buscando produto ID: {PRODUTO_ID}")
print(f"URL: {url}\n")

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        produto = response.json()
        print("✓ Produto encontrado!")
        print(json.dumps(produto, indent=2, ensure_ascii=False))
    else:
        print(f"✗ Erro {response.status_code}")
        try:
            erro = response.json()
            print(json.dumps(erro, indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
except Exception as e:
    print(f"✗ Erro na requisicao: {str(e)}")
