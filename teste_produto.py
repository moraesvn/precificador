import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Carregar variaveis do .env
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")
PRODUTO_ID = os.getenv("TINY_PRODUTO_ID")

print("=" * 60)
print("TESTE SIMPLES - API PRODUTOS V3 TINY/OLIST")
print("=" * 60)

# Verificar se tem access token
if not ACCESS_TOKEN:
    print("\n[ERRO] TINY_ACCESS_TOKEN nao encontrado no .env")
    print("[DICA] Execute primeiro o teste.py para obter o access token")
    exit(1)

# Verificar se tem ID do produto
if not PRODUTO_ID:
    print("\n[AVISO] TINY_PRODUTO_ID nao encontrado no .env")
    print("[INFO] Testando listagem de produtos (sem ID especifico)")
    TEST_URL = "https://api.tiny.com.br/public-api/v3/produtos"
else:
    print(f"\n[INFO] Testando produto ID: {PRODUTO_ID}")
    TEST_URL = f"https://api.tiny.com.br/public-api/v3/produtos/{PRODUTO_ID}"

# Fazer requisicao
print(f"\n[REQUISICAO] GET {TEST_URL}")
print(f"[TOKEN] {ACCESS_TOKEN[:30]}...")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(TEST_URL, headers=headers)
    
    print(f"\n[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        print("[OK] Sucesso! Resposta da API:")
        print("=" * 60)
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 60)
    else:
        print(f"[ERRO] Falha na requisicao")
        print(f"[RESPOSTA] {response.text[:500]}")
        
except Exception as e:
    print(f"[ERRO] Erro na requisicao: {str(e)}")

print("\n" + "=" * 60)
