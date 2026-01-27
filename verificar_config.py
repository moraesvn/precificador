import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

print("=" * 60)
print("VERIFICACAO DE CONFIGURACAO - API V3 TINY/OLIST")
print("=" * 60)

# Verificar todas as variáveis
CLIENT_ID = os.getenv("TINY_CLIENT_ID")
CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET")
AUTHORIZATION_CODE = os.getenv("TINY_AUTHORIZATION_CODE")
REDIRECT_URI = os.getenv("TINY_REDIRECT_URI")
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("TINY_REFRESH_TOKEN")

erros = []
avisos = []

# Verificar CLIENT_ID
if not CLIENT_ID:
    erros.append("TINY_CLIENT_ID nao encontrado no .env")
else:
    print(f"✓ TINY_CLIENT_ID: {CLIENT_ID[:20]}...")

# Verificar CLIENT_SECRET
if not CLIENT_SECRET:
    erros.append("TINY_CLIENT_SECRET nao encontrado no .env")
else:
    print(f"✓ TINY_CLIENT_SECRET: {'*' * 20}...")

# Verificar REDIRECT_URI
if not REDIRECT_URI:
    erros.append("TINY_REDIRECT_URI nao encontrado no .env")
else:
    REDIRECT_URI = REDIRECT_URI.strip()
    print(f"✓ TINY_REDIRECT_URI: {REDIRECT_URI}")
    
    # Validar formato da URL
    try:
        parsed = urlparse(REDIRECT_URI)
        if not parsed.scheme or not parsed.netloc:
            avisos.append(f"REDIRECT_URI pode estar em formato invalido: {REDIRECT_URI}")
    except:
        avisos.append(f"REDIRECT_URI pode estar em formato invalido: {REDIRECT_URI}")

# Verificar AUTHORIZATION_CODE
if not AUTHORIZATION_CODE:
    avisos.append("TINY_AUTHORIZATION_CODE nao encontrado (necessario para obter token)")
else:
    AUTHORIZATION_CODE = AUTHORIZATION_CODE.strip()
    print(f"✓ TINY_AUTHORIZATION_CODE: {AUTHORIZATION_CODE[:30]}... (tamanho: {len(AUTHORIZATION_CODE)} caracteres)")
    
    # Verificar problemas comuns no código
    if ' ' in AUTHORIZATION_CODE:
        avisos.append("AUTHORIZATION_CODE contem espacos - pode causar problemas")
    if '\n' in AUTHORIZATION_CODE or '\r' in AUTHORIZATION_CODE:
        avisos.append("AUTHORIZATION_CODE contem quebras de linha - pode causar problemas")
    if len(AUTHORIZATION_CODE) < 20:
        avisos.append("AUTHORIZATION_CODE parece muito curto - verifique se foi copiado completamente")

# Verificar tokens existentes
if ACCESS_TOKEN:
    print(f"✓ TINY_ACCESS_TOKEN: {ACCESS_TOKEN[:30]}... (tamanho: {len(ACCESS_TOKEN)} caracteres)")
else:
    avisos.append("TINY_ACCESS_TOKEN nao encontrado (sera necessario obter um)")

if REFRESH_TOKEN:
    print(f"✓ TINY_REFRESH_TOKEN: {REFRESH_TOKEN[:30]}... (tamanho: {len(REFRESH_TOKEN)} caracteres)")

print("\n" + "=" * 60)

# Mostrar erros
if erros:
    print("[ERROS ENCONTRADOS]")
    for erro in erros:
        print(f"  ✗ {erro}")
    print()

# Mostrar avisos
if avisos:
    print("[AVISOS]")
    for aviso in avisos:
        print(f"  ⚠ {aviso}")
    print()

# Resumo
if erros:
    print("=" * 60)
    print("[RESULTADO] Configuracao INCOMPLETA")
    print("Corrija os erros acima antes de continuar")
    print("=" * 60)
elif avisos:
    print("=" * 60)
    print("[RESULTADO] Configuracao OK com avisos")
    print("Revise os avisos acima")
    print("=" * 60)
else:
    print("=" * 60)
    print("[RESULTADO] Configuracao OK")
    print("=" * 60)

# Instruções
if not AUTHORIZATION_CODE and not ACCESS_TOKEN:
    print("\n[PROXIMOS PASSOS]")
    print("1. Execute: python obter_authorization_code.py")
    print("2. Acesse a URL gerada no navegador")
    print("3. Copie o codigo da URL de callback")
    print("4. Adicione no .env: TINY_AUTHORIZATION_CODE=seu_codigo")
    print("5. Execute IMEDIATAMENTE: python obter_token.py")
elif AUTHORIZATION_CODE and not ACCESS_TOKEN:
    print("\n[PROXIMOS PASSOS]")
    print("1. Execute IMEDIATAMENTE: python obter_token.py")
    print("   (O codigo expira rapidamente!)")
elif ACCESS_TOKEN:
    print("\n[STATUS]")
    print("Voce ja tem um access token configurado")
    print("Se o token expirou, gere um novo codigo de autorizacao")

print("=" * 60)
