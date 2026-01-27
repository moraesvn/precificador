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
print("\n" + "=" * 60)
print("[⚠️  ATENCAO - MUITO IMPORTANTE!]")
print("=" * 60)
print("1. O codigo expira em POUCOS MINUTOS (geralmente 1-2 minutos)")
print("2. O codigo so pode ser usado UMA VEZ (single-use)")
print("3. Use o codigo IMEDIATAMENTE apos obte-lo")
print("4. Apos obter o codigo:")
print("   a) Copie o codigo EXATO da URL (sem espacos)")
print("   b) Adicione no .env: TINY_AUTHORIZATION_CODE=seu_codigo_aqui")
print("   c) Execute obter_token.py IMEDIATAMENTE")
print("5. O REDIRECT_URI usado aqui DEVE ser EXATAMENTE o mesmo")
print(f"   configurado no .env: {REDIRECT_URI}")
print("   (incluindo / no final se houver)")
print("=" * 60)
