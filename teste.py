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

print("=" * 60)
print("🧪 TESTE DE AUTORIZAÇÃO API V3 TINY")
print("=" * 60)

# Se já temos access token, testa diretamente
if ACCESS_TOKEN:
    print("\n✅ Access token encontrado no .env")
    print(f"Token: {ACCESS_TOKEN[:20]}...")
    
    # Testar autorização com uma requisição de teste
    print("\n🧪 Testando autorização...")
    TEST_URL = "https://api.tiny.com.br/api/v3/contas/informacoes"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(TEST_URL, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            print("✅ Autorização confirmada! Acesso à API V3 funcionando.")
            print("\n📋 Informações da conta:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro ao testar autorização: {response.status_code}")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")

# Se não temos access token mas temos authorization code, tenta obter
elif AUTHORIZATION_CODE and CLIENT_ID and CLIENT_SECRET:
    print("\n🔐 Obtendo access token usando authorization code...")
    
    TOKEN_URL = "https://api.tiny.com.br/oauth/access_token"
    
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": AUTHORIZATION_CODE
    }
    
    try:
        token_response = requests.post(TOKEN_URL, data=token_payload)
        token_data = token_response.json()
        
        if token_response.status_code == 200:
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            
            print("✅ Access token obtido com sucesso!")
            print(f"Access Token: {access_token[:20]}...")
            if refresh_token:
                print(f"Refresh Token: {refresh_token[:20]}...")
            
            # Agora testa a autorização
            print("\n🧪 Testando autorização...")
            TEST_URL = "https://api.tiny.com.br/api/v3/contas/informacoes"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            test_response = requests.get(TEST_URL, headers=headers)
            test_data = test_response.json()
            
            if test_response.status_code == 200:
                print("✅ Autorização confirmada! Acesso à API V3 funcionando.")
                print("\n📋 Informações da conta:")
                print(json.dumps(test_data, indent=2, ensure_ascii=False))
                
                print("\n💡 IMPORTANTE: Salve estes tokens no seu .env:")
                print(f"TINY_ACCESS_TOKEN={access_token}")
                if refresh_token:
                    print(f"TINY_REFRESH_TOKEN={refresh_token}")
            else:
                print(f"❌ Erro ao testar autorização: {test_response.status_code}")
                print(json.dumps(test_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro ao obter access token: {token_response.status_code}")
            print(json.dumps(token_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")

else:
    print("\n❌ Variáveis não encontradas no .env")
    print("\nVocê precisa ter uma das seguintes opções:")
    print("1. TINY_ACCESS_TOKEN (para testar diretamente)")
    print("2. TINY_CLIENT_ID, TINY_CLIENT_SECRET e TINY_AUTHORIZATION_CODE (para obter token)")
    print("\nVariáveis encontradas:")
    print(f"  CLIENT_ID: {'✅' if CLIENT_ID else '❌'}")
    print(f"  CLIENT_SECRET: {'✅' if CLIENT_SECRET else '❌'}")
    print(f"  AUTHORIZATION_CODE: {'✅' if AUTHORIZATION_CODE else '❌'}")
    print(f"  ACCESS_TOKEN: {'✅' if ACCESS_TOKEN else '❌'}")

print("\n" + "=" * 60)
