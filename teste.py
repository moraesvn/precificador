import requests
from dotenv import load_dotenv
import os, json

load_dotenv()

token = os.getenv("TINY_TOKEN")
product_id = os.getenv("TINY_PRODUCT_ID")

url = "https://api.tiny.com.br/api2/produtos.pesquisa.php"
payload = {
    "token": token,
    "id": 116,
    "formato": "JSON"
}

response = requests.post(url, data=payload)
data = response.json()

# imprime o JSON bem formatado
print(json.dumps(data, indent=2, ensure_ascii=False))
