import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Credenciais OAuth2
CLIENT_ID = os.getenv("TINY_CLIENT_ID")
CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET")
AUTHORIZATION_CODE = os.getenv("TINY_AUTHORIZATION_CODE")
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")
REDIRECT_URI = os.getenv("TINY_REDIRECT_URI")  # URL de redirecionamento configurada no Tiny
PRODUTO_ID = os.getenv("TINY_PRODUTO_ID")  # ID do produto para teste (opcional)

print("=" * 60)
print("TESTE DE AUTORIZACAO API V3 TINY/OLIST")
print("=" * 60)

# Se já temos access token, testa diretamente
if ACCESS_TOKEN:
    print("\n[OK] Access token encontrado no .env")
    print(f"Token: {ACCESS_TOKEN[:20]}...")
    
    # Testar autorização com uma requisição de teste - API de produtos
    print("\n[TESTE] Testando autorizacao com API de produtos...")
    
    # Se tem ID de produto, usa ele, senao tenta listar produtos
    if PRODUTO_ID:
        TEST_URL = f"https://api.tiny.com.br/public-api/v3/produtos/{PRODUTO_ID}"
        print(f"[INFO] Testando produto ID: {PRODUTO_ID}")
    else:
        # Tenta listar produtos (endpoint comum em APIs REST)
        TEST_URL = "https://api.tiny.com.br/public-api/v3/produtos"
        print("[INFO] Testando listagem de produtos (sem ID especifico)")
        print("[DICA] Para testar produto especifico, adicione TINY_PRODUTO_ID no .env")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(TEST_URL, headers=headers)
        
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] URL: {TEST_URL}")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"[ERRO] Resposta nao e um JSON valido")
            print(f"Resposta completa: {response.text[:500]}")
            data = {}
        
        if response.status_code == 200:
            print("[OK] Autorizacao confirmada! Acesso a API V3 funcionando.")
            print("\n[INFO] Resposta da API:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"[ERRO] Erro ao testar autorizacao: {response.status_code}")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[ERRO] Erro na requisicao: {str(e)}")

# Se não temos access token mas temos authorization code, tenta obter
elif AUTHORIZATION_CODE and CLIENT_ID and CLIENT_SECRET:
    print("\n[OBTENDO] Obtendo access token usando authorization code...")
    
    # Endpoint correto conforme documentacao oficial da API V3
    # https://api-docs.erp.olist.com/documentacao/comecando/autenticacao
    TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"
    
    # Preparar payload conforme documentacao oficial
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": AUTHORIZATION_CODE,
    }
    
    # redirect_uri e obrigatorio conforme documentacao
    if REDIRECT_URI:
        token_payload["redirect_uri"] = REDIRECT_URI
        print(f"[INFO] Usando redirect_uri: {REDIRECT_URI}")
    else:
        print("[ERRO] REDIRECT_URI e obrigatorio!")
        print("[ERRO] Adicione TINY_REDIRECT_URI no seu .env")
        token_response = None
    
    if REDIRECT_URI:
        print(f"\n[REQUISICAO] Endpoint: {TOKEN_URL}")
        
        try:
            # Conforme documentacao: Content-Type: application/x-www-form-urlencoded
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            token_response = requests.post(TOKEN_URL, data=token_payload, headers=headers)
            
            print(f"[DEBUG] Status Code: {token_response.status_code}")
            
            if token_response.status_code == 200:
                print(f"[OK] Token obtido com sucesso!")
            elif token_response.status_code == 400:
                print(f"[ERRO] Status 400 - Bad Request")
                try:
                    error_data = token_response.json()
                    print(f"[ERRO] Detalhes: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"[ERRO] Resposta: {token_response.text[:500]}")
            elif token_response.status_code == 401:
                print(f"[ERRO] Status 401 - Unauthorized")
                print(f"[ERRO] Credenciais incorretas ou authorization code expirado")
                try:
                    error_data = token_response.json()
                    print(f"[ERRO] Detalhes: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"[ERRO] Resposta: {token_response.text[:500]}")
            else:
                print(f"[ERRO] Status {token_response.status_code}")
                print(f"[ERRO] Resposta: {token_response.text[:500]}")
                
        except Exception as e:
            print(f"[ERRO] Erro na requisicao: {str(e)}")
            token_response = None
    
    if token_response and token_response.status_code == 200:
        try:
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            
            if access_token:
                print("\n[OK] Access token obtido com sucesso!")
                print(f"Access Token: {access_token[:30]}...")
                if refresh_token:
                    print(f"Refresh Token: {refresh_token[:30]}...")
                if expires_in:
                    print(f"Expira em: {expires_in} segundos")
                
                # Agora testa a autorização com API de produtos
                print("\n[TESTE] Testando autorizacao com API de produtos...")
                
                # Se tem ID de produto, usa ele, senao tenta listar produtos
                if PRODUTO_ID:
                    TEST_URL = f"https://api.tiny.com.br/public-api/v3/produtos/{PRODUTO_ID}"
                    print(f"[INFO] Testando produto ID: {PRODUTO_ID}")
                else:
                    # Tenta listar produtos
                    TEST_URL = "https://api.tiny.com.br/public-api/v3/produtos"
                    print("[INFO] Testando listagem de produtos (sem ID especifico)")
                    print("[DICA] Para testar produto especifico, adicione TINY_PRODUTO_ID no .env")
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                test_response = requests.get(TEST_URL, headers=headers)
                
                print(f"[DEBUG] Status Code: {test_response.status_code}")
                print(f"[DEBUG] URL: {TEST_URL}")
                
                try:
                    test_data = test_response.json()
                except json.JSONDecodeError:
                    print(f"[ERRO] Resposta nao e um JSON valido")
                    print(f"Resposta completa: {test_response.text[:500]}")
                    test_data = {}
                
                if test_response.status_code == 200:
                    print("[OK] Autorizacao confirmada! Acesso a API V3 funcionando.")
                    print("\n[INFO] Resposta da API:")
                    print(json.dumps(test_data, indent=2, ensure_ascii=False))
                    
                    print("\n" + "=" * 60)
                    print("[IMPORTANTE] Salve estes tokens no seu .env:")
                    print("=" * 60)
                    print(f"TINY_ACCESS_TOKEN={access_token}")
                    if refresh_token:
                        print(f"TINY_REFRESH_TOKEN={refresh_token}")
                    print("=" * 60)
                else:
                    print(f"[ERRO] Erro ao testar autorizacao: {test_response.status_code}")
                    print(json.dumps(test_data, indent=2, ensure_ascii=False))
            else:
                print("[ERRO] Access token nao encontrado na resposta")
                print(json.dumps(token_data, indent=2, ensure_ascii=False))
                
        except json.JSONDecodeError:
            print(f"[ERRO] Resposta nao e um JSON valido")
            print(f"Resposta completa: {token_response.text}")
    else:
        print("\n" + "=" * 60)
        print("[ERRO] Nao foi possivel obter o access token")
        print("=" * 60)
        print("\n[INFO] Possiveis problemas:")
        print("  1. Authorization code pode ter expirado (geralmente expira em poucos minutos)")
        print("  2. URL do endpoint pode estar incorreta")
        print("  3. redirect_uri pode ser obrigatorio e nao foi fornecido")
        print("  4. Client ID ou Client Secret podem estar incorretos")
        print("  5. A URL de redirecionamento deve ser EXATAMENTE a mesma configurada no painel")
        print("\n[ACAO] Consulte a documentacao oficial:")
        print("  https://api-docs.erp.olist.com/documentacao/comecando/autenticacao")
        print("\n[INFO] Variaveis encontradas:")
        print(f"  CLIENT_ID: {'[OK]' if CLIENT_ID else '[FALTANDO]'}")
        print(f"  CLIENT_SECRET: {'[OK]' if CLIENT_SECRET else '[FALTANDO]'}")
        print(f"  AUTHORIZATION_CODE: {'[OK]' if AUTHORIZATION_CODE else '[FALTANDO]'}")
        print(f"  REDIRECT_URI: {'[OK]' if REDIRECT_URI else '[FALTANDO - PODE SER OBRIGATORIO]'}")

else:
    print("\n[ERRO] Variaveis nao encontradas no .env")
    print("\nVoce precisa ter uma das seguintes opcoes:")
    print("1. TINY_ACCESS_TOKEN (para testar diretamente)")
    print("2. TINY_CLIENT_ID, TINY_CLIENT_SECRET e TINY_AUTHORIZATION_CODE (para obter token)")
    print("\nVariaveis encontradas:")
    print(f"  CLIENT_ID: {'[OK]' if CLIENT_ID else '[FALTANDO]'}")
    print(f"  CLIENT_SECRET: {'[OK]' if CLIENT_SECRET else '[FALTANDO]'}")
    print(f"  AUTHORIZATION_CODE: {'[OK]' if AUTHORIZATION_CODE else '[FALTANDO]'}")
    print(f"  ACCESS_TOKEN: {'[OK]' if ACCESS_TOKEN else '[FALTANDO]'}")

print("\n" + "=" * 60)
