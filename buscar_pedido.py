import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Carregar access token
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERRO: TINY_ACCESS_TOKEN nao encontrado no .env")
    exit(1)

# Limpar token
ACCESS_TOKEN = ACCESS_TOKEN.strip()

# ID do pedido
PEDIDO_ID = 298311

# URL da API
url = f"https://api.tiny.com.br/public-api/v3/pedidos/{PEDIDO_ID}"

# Headers
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

print(f"[REQUISICAO] GET {url}")
print(f"[TOKEN] {ACCESS_TOKEN[:30]}... (tamanho: {len(ACCESS_TOKEN)} caracteres)\n")

try:
    response = requests.get(url, headers=headers)
    
    print(f"[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        print("[OK] Pedido encontrado!")
        print("=" * 60)
        print(response.text)
        print("=" * 60)
    elif response.status_code == 401:
        print("[ERRO] 401 - Token invalido ou expirado")
        print("\n[RESPOSTA DA API]")
        print(response.text)
        print("\n[SOLUCAO]")
        print("Execute: python renovar_token.py")
    else:
        print(f"[ERRO] Status {response.status_code}")
        print("\n[RESPOSTA]")
        print(response.text)
        
except Exception as e:
    print(f"[ERRO] Erro na requisicao: {str(e)}")
