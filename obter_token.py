import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Credenciais OAuth2
CLIENT_ID = os.getenv("TINY_CLIENT_ID")
CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET")
AUTHORIZATION_CODE = os.getenv("TINY_AUTHORIZATION_CODE")
REDIRECT_URI = os.getenv("TINY_REDIRECT_URI")

print("=" * 60)
print("OBTER ACCESS TOKEN - API V3 TINY/OLIST")
print("=" * 60)

# Verificar variaveis necessarias
if not CLIENT_ID:
    print("\n[ERRO] TINY_CLIENT_ID nao encontrado no .env")
    exit(1)

if not CLIENT_SECRET:
    print("\n[ERRO] TINY_CLIENT_SECRET nao encontrado no .env")
    exit(1)

if not AUTHORIZATION_CODE:
    print("\n[ERRO] TINY_AUTHORIZATION_CODE nao encontrado no .env")
    print("[DICA] Execute obter_authorization_code.py para gerar a URL de autorizacao")
    exit(1)

if not REDIRECT_URI:
    print("\n[ERRO] TINY_REDIRECT_URI nao encontrado no .env")
    exit(1)

# Endpoint conforme documentacao oficial
TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"

# Preparar payload
token_payload = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": AUTHORIZATION_CODE,
    "redirect_uri": REDIRECT_URI
}

print(f"\n[REQUISICAO] POST {TOKEN_URL}")
print(f"[CLIENT_ID] {CLIENT_ID[:20]}...")
print(f"[CODE] {AUTHORIZATION_CODE[:20]}...")

# Fazer requisicao
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

try:
    response = requests.post(TOKEN_URL, data=token_payload, headers=headers)
    
    print(f"\n[STATUS] {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        
        print("\n[OK] Access token obtido com sucesso!")
        print("=" * 60)
        print("[IMPORTANTE] Adicione estes tokens no seu .env:")
        print("=" * 60)
        print(f"TINY_ACCESS_TOKEN={access_token}")
        if refresh_token:
            print(f"TINY_REFRESH_TOKEN={refresh_token}")
        print("=" * 60)
        
        if expires_in:
            horas = expires_in // 3600
            minutos = (expires_in % 3600) // 60
            print(f"\n[INFO] Access token expira em: {horas}h {minutos}min")
        
        if refresh_token:
            print(f"[INFO] Refresh token expira em: 1 dia")
    else:
        print(f"\n[ERRO] Falha ao obter token")
        try:
            error_data = response.json()
            print(f"[DETALHES] {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"[RESPOSTA] {response.text[:500]}")
            
except Exception as e:
    print(f"\n[ERRO] Erro na requisicao: {str(e)}")

print("\n" + "=" * 60)
