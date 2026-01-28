import requests
from dotenv import load_dotenv
import os
import sys
import json
from urllib.parse import urlparse, parse_qs

load_dotenv()

print("=" * 60)
print("OBTER TOKEN AUTOMATICO - API V3 TINY/OLIST")
print("=" * 60)

# Verificar se a URL ou código foi passado como argumento
if len(sys.argv) > 1:
    url_input = sys.argv[1].strip()
    
    # Tentar extrair código da URL
    if "code=" in url_input or "http" in url_input:
        try:
            parsed = urlparse(url_input)
            params = parse_qs(parsed.query)
            if 'code' in params:
                AUTHORIZATION_CODE = params['code'][0].strip()
                print(f"\n[INFO] Codigo extraido da URL")
            else:
                AUTHORIZATION_CODE = url_input.strip()
        except:
            AUTHORIZATION_CODE = url_input.strip()
    else:
        AUTHORIZATION_CODE = url_input.strip()
else:
    # Pedir URL ou código ao usuário
    print("\n[INFO] Cole a URL completa de callback OU apenas o codigo:")
    print("Exemplo URL: https://gpprecificador.streamlit.app/?code=ABC123...")
    print("Exemplo codigo: ABC123XYZ")
    user_input = input("\nCole aqui: ").strip()
    
    if "code=" in user_input or "http" in user_input:
        # Extrair código da URL
        try:
            parsed = urlparse(user_input)
            params = parse_qs(parsed.query)
            if 'code' in params:
                AUTHORIZATION_CODE = params['code'][0].strip()
                print(f"\n[INFO] Codigo extraido da URL: {AUTHORIZATION_CODE[:30]}...")
            else:
                AUTHORIZATION_CODE = user_input.strip()
        except:
            AUTHORIZATION_CODE = user_input.strip()
    else:
        AUTHORIZATION_CODE = user_input.strip()

if not AUTHORIZATION_CODE:
    print("\n[ERRO] Codigo de autorizacao nao fornecido")
    exit(1)

# Carregar credenciais
CLIENT_ID = os.getenv("TINY_CLIENT_ID")
CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TINY_REDIRECT_URI")

if not CLIENT_ID:
    print("\n[ERRO] TINY_CLIENT_ID nao encontrado no .env")
    exit(1)

if not CLIENT_SECRET:
    print("\n[ERRO] TINY_CLIENT_SECRET nao encontrado no .env")
    exit(1)

if not REDIRECT_URI:
    print("\n[ERRO] TINY_REDIRECT_URI nao encontrado no .env")
    exit(1)

# Limpar o código
AUTHORIZATION_CODE = AUTHORIZATION_CODE.strip()

print(f"\n[DEBUG] Codigo: {AUTHORIZATION_CODE[:30]}... (tamanho: {len(AUTHORIZATION_CODE)} caracteres)")
print(f"[DEBUG] REDIRECT_URI: {REDIRECT_URI}")

# Endpoint
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
print("[AGUARDANDO] Gerando tokens...")

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
        
        print("\n" + "=" * 60)
        print("✅ TOKENS GERADOS COM SUCESSO!")
        print("=" * 60)
        
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
            print(f"[INFO] Refresh token expira em: 1 dia")
        
        # Tentar salvar automaticamente no .env
        try:
            env_path = ".env"
            if os.path.exists(env_path):
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
                
                print("\n✅ Tokens salvos automaticamente no .env!")
            else:
                print("\n⚠️ Arquivo .env nao encontrado. Copie os tokens manualmente.")
        except Exception as e:
            print(f"\n⚠️ Nao foi possivel salvar automaticamente: {str(e)}")
            print("Copie os tokens manualmente para o .env")
            
    else:
        print(f"\n[ERRO] Falha ao obter token")
        try:
            error_data = response.json()
            print(f"[DETALHES] {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            
            if error_data.get("error") == "invalid_grant":
                print("\n" + "=" * 60)
                print("[ERRO] Codigo invalido ou expirado")
                print("=" * 60)
                print("Possiveis causas:")
                print("1. Codigo expirou (validade: 1-2 minutos)")
                print("2. Codigo ja foi usado (single-use)")
                print("3. REDIRECT_URI nao corresponde")
                print(f"   REDIRECT_URI atual: {REDIRECT_URI}")
                print("\n[SOLUCAO]")
                print("1. Gere um novo codigo com obter_authorization_code.py")
                print("2. Use este script IMEDIATAMENTE apos obter o codigo")
                print("   Exemplo: python obter_token_automatico.py <codigo_ou_url>")
                print("=" * 60)
        except:
            print(f"[RESPOSTA] {response.text[:500]}")
            
except Exception as e:
    print(f"\n[ERRO] Erro na requisicao: {str(e)}")

print("\n" + "=" * 60)
