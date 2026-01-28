import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

st.set_page_config(page_title="Callback Tiny V3", page_icon="🔐")

st.title('Callback Tiny - Autorização OAuth2')
st.write("Esta página recebe o código de autorização após o usuário autorizar o aplicativo.")

params = st.query_params  # Streamlit Cloud já traz os params

# Verificar se tem o código de autorização
if 'code' in params:
    authorization_code = params['code'][0] if isinstance(params['code'], list) else params['code']
    
    st.success("✅ Código de autorização recebido com sucesso!")
    
    # Carregar credenciais
    CLIENT_ID = os.getenv("TINY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("TINY_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("TINY_REDIRECT_URI")
    
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        st.error("⚠️ Credenciais não encontradas nas variáveis de ambiente")
        st.info("Configure TINY_CLIENT_ID, TINY_CLIENT_SECRET e TINY_REDIRECT_URI")
    else:
        # Gerar token automaticamente
        with st.spinner("🔄 Gerando tokens..."):
            TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"
            
            token_payload = {
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": authorization_code.strip(),
                "redirect_uri": REDIRECT_URI.strip()
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            try:
                response = requests.post(TOKEN_URL, data=token_payload, headers=headers)
                
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data.get("access_token")
                    refresh_token = token_data.get("refresh_token")
                    expires_in = token_data.get("expires_in")
                    
                    st.success("✅ Tokens gerados com sucesso!")
                    
                    # Mostrar informações dos tokens
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🔑 Access Token")
                        st.code(access_token, language=None)
                        if expires_in:
                            horas = expires_in // 3600
                            minutos = (expires_in % 3600) // 60
                            st.info(f"⏰ Expira em: {horas}h {minutos}min")
                    
                    with col2:
                        if refresh_token:
                            st.subheader("🔄 Refresh Token")
                            st.code(refresh_token, language=None)
                            st.info("⏰ Expira em: 1 dia")
                    
                    # Mostrar tokens para copiar
                    st.subheader("📋 Tokens para adicionar no .env:")
                    st.code(f"""TINY_ACCESS_TOKEN={access_token}
TINY_REFRESH_TOKEN={refresh_token}""", language=None)
                    
                    # Tentar salvar em variável de sessão (para uso no Streamlit)
                    st.session_state['tiny_access_token'] = access_token
                    if refresh_token:
                        st.session_state['tiny_refresh_token'] = refresh_token
                    
                    st.info("💡 Os tokens foram salvos na sessão do Streamlit e podem ser usados nas requisições desta página.")
                    
                elif response.status_code == 400:
                    st.error("❌ Erro ao gerar tokens")
                    try:
                        error_data = response.json()
                        if error_data.get("error") == "invalid_grant":
                            st.warning("⚠️ Código inválido ou expirado")
                            st.write("**Possíveis causas:**")
                            st.write("1. Código expirou (validade: 1-2 minutos)")
                            st.write("2. Código já foi usado (single-use)")
                            st.write("3. REDIRECT_URI não corresponde")
                        st.json(error_data)
                    except:
                        st.text(response.text)
                else:
                    st.error(f"❌ Erro {response.status_code}")
                    st.text(response.text[:500])
                    
            except Exception as e:
                st.error(f"❌ Erro na requisição: {str(e)}")
    
    # Mostrar código original também
    st.divider()
    st.subheader("📋 Código de Autorização Original:")
    st.code(authorization_code, language=None)
    
    # Mostrar todos os parâmetros recebidos
    st.subheader("📄 Todos os parâmetros recebidos:")
    st.json(dict(params))
    
elif 'error' in params:
    error = params['error'][0] if isinstance(params['error'], list) else params['error']
    st.error(f"❌ Erro na autorização: {error}")
    if 'error_description' in params:
        error_desc = params['error_description'][0] if isinstance(params['error_description'], list) else params['error_description']
        st.write(f"**Descrição:** {error_desc}")
    st.json(dict(params))
else:
    st.warning("⚠️ Aguardando código de autorização...")
    st.write("**Parâmetros recebidos:**")
    st.json(dict(params))
    st.info("""
    **Como obter o código:**
    1. Execute o script `obter_authorization_code.py` para gerar a URL de autorização
    2. Acesse a URL gerada no navegador
    3. Faça login e autorize o aplicativo
    4. Você será redirecionado para esta página e os tokens serão gerados automaticamente
    """)

