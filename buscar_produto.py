import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Carregar access token
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("ERRO: TINY_ACCESS_TOKEN nao encontrado no .env")
    exit(1)

# ID do produto
#PRODUTO_ID = 7113

# URL da API
url = "https://api.tiny.com.br/public-api/v3/produtos?limit=100&codigo=7113"

# Headers
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# Fazer requisicao
response = requests.get(url, headers=headers)

print(response.text)
