import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TINY_CLIENT_ID")
REDIRECT_URI = os.getenv("TINY_REDIRECT_URI")

print("=" * 60)
print("GERAR URL DE AUTORIZACAO - API V3 TINY/OLIST")
print("=" * 60)

if not CLIENT_ID:
    print("\n[ERRO] TINY_CLIENT_ID nao encontrado no .env")
    exit(1)

if not REDIRECT_URI:
    print("\n[ERRO] TINY_REDIRECT_URI nao encontrado no .env")
    exit(1)

# URL de autorizacao conforme documentacao oficial
auth_url = (
    f"https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=openid"
    f"&response_type=code"
)

print("\n[INFO] URL de autorizacao gerada:")
print("=" * 60)
print(auth_url)
print("=" * 60)

print("\n[INSTRUCOES]")
print("1. Copie a URL acima e cole no seu navegador")
print("2. Faca login na conta do Tiny/Olist")
print("3. Autorize o aplicativo")
print("4. Voce sera redirecionado para sua URL de callback")
print("5. O codigo de autorizacao estara no parametro 'code' da URL")
print("\n[EXEMPLO]")
print("URL de callback: https://seu-app.com/?code=ABC123XYZ&state=...")
print("O codigo seria: ABC123XYZ")
print("\n[IMPORTANTE]")
print("- O codigo expira rapidamente (alguns minutos)")
print("- Apos obter o codigo, adicione no .env:")
print("  TINY_AUTHORIZATION_CODE=ABC123XYZ")
print("=" * 60)
