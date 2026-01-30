import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

print("=" * 60)
print("RENOVAR ACCESS TOKEN - API V3 TINY/OLIST")
print("=" * 60)

CLIENT_ID = os.getenv("TINY_CLIENT_ID")
CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("TINY_REFRESH_TOKEN")

# Verificar variaveis necessarias
if not CLIENT_ID:
    print("\n[ERRO] TINY_CLIENT_ID nao encontrado no .env")
    exit(1)

if not CLIENT_SECRET:
    print("\n[ERRO] TINY_CLIENT_SECRET nao encontrado no .env")
    exit(1)

if not REFRESH_TOKEN:
    print("\n[ERRO] TINY_REFRESH_TOKEN nao encontrado no .env")
    print("[DICA] Execute obter_token.py primeiro para obter o refresh token")
    exit(1)

REFRESH_TOKEN = REFRESH_TOKEN.strip()

# Endpoint conforme documentacao oficial
TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"

# Preparar payload
token_payload = {
    "grant_type": "refresh_token",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "refresh_token": REFRESH_TOKEN
}

print(f"\n[REQUISICAO] POST {TOKEN_URL}")
print(f"[CLIENT_ID] {CLIENT_ID[:20]}...")
print(f"[REFRESH_TOKEN] {REFRESH_TOKEN[:30]}...")

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
        
        print("\n[OK] Access token renovado com sucesso!")
        
        # Salvar automaticamente no .env
        env_path = ".env"
        if os.path.exists(env_path):
            try:
                # Ler arquivo .env
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Atualizar ou adicionar tokens
                new_lines = []
                access_token_found = False
                refresh_token_found = False
                
                for line in lines:
                    if line.startswith("TINY_ACCESS_TOKEN="):
                        new_lines.append(f"TINY_ACCESS_TOKEN={access_token}\n")
                        access_token_found = True
                    elif line.startswith("TINY_REFRESH_TOKEN="):
                        if refresh_token:
                            new_lines.append(f"TINY_REFRESH_TOKEN={refresh_token}\n")
                        refresh_token_found = True
                    else:
                        new_lines.append(line)
                
                # Adicionar se não existir
                if not access_token_found:
                    new_lines.append(f"\nTINY_ACCESS_TOKEN={access_token}\n")
                if refresh_token and not refresh_token_found:
                    new_lines.append(f"TINY_REFRESH_TOKEN={refresh_token}\n")
                
                # Salvar arquivo
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print("=" * 60)
                print("✅ Tokens salvos automaticamente no .env!")
                print("=" * 60)
                
            except Exception as e:
                print("=" * 60)
                print("⚠️ Nao foi possivel salvar automaticamente no .env")
                print(f"Erro: {str(e)}")
                print("\n[IMPORTANTE] Atualize manualmente estes tokens no .env:")
                print("=" * 60)
                print(f"TINY_ACCESS_TOKEN={access_token}")
                if refresh_token:
                    print(f"TINY_REFRESH_TOKEN={refresh_token}")
                print("=" * 60)
        else:
            print("=" * 60)
            print("⚠️ Arquivo .env nao encontrado")
            print("\n[IMPORTANTE] Adicione estes tokens no seu .env:")
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
            print(f"[INFO] Refresh token renovado (validade: 1 dia)")
    else:
        print(f"\n[ERRO] Falha ao renovar token")
        try:
            error_data = response.json()
            print(f"[DETALHES] {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            
            if error_data.get("error") == "invalid_grant":
                print("\n[POSSIVEIS CAUSAS]")
                print("1. Refresh token expirou (validade: 1 dia)")
                print("2. Refresh token foi revogado")
                print("3. Refresh token invalido")
                print("\n[SOLUCAO]")
                print("Execute obter_authorization_code.py e depois obter_token.py")
        except:
            print(f"[RESPOSTA] {response.text[:500]}")
            
except Exception as e:
    print(f"\n[ERRO] Erro na requisicao: {str(e)}")

print("\n" + "=" * 60)
