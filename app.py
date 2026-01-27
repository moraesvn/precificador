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
    
    st.subheader("📋 Código de Autorização:")
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
    4. Você será redirecionado para esta página com o código
    """)

'''


# Seção para teste de API de produtos
st.divider()
st.subheader("🧪 Teste de API - Buscar Produto")

# Carregar access token
ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    st.error("⚠️ TINY_ACCESS_TOKEN não encontrado nas variáveis de ambiente")
    st.info("Configure o token nas variáveis de ambiente do Streamlit Cloud ou no arquivo .env")
else:
    ACCESS_TOKEN = ACCESS_TOKEN.strip()
    
    # Campo para código do produto
    codigo_produto = st.text_input(
        "Código do Produto",
        value="7113",
        help="Digite o código do produto que deseja buscar"
    )
    
    # Botão para fazer requisição
    if st.button("🔍 Buscar Produto", type="primary"):
        if codigo_produto:
            with st.spinner("Buscando produto..."):
                # URL da API
                url = f"https://api.tiny.com.br/public-api/v3/produtos?limit=100&codigo={codigo_produto}"
                
                # Headers
                headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
                
                try:
                    response = requests.get(url, headers=headers)
                    
                    st.write(f"**Status:** {response.status_code}")
                    st.write(f"**URL:** `{url}`")
                    
                    if response.status_code == 200:
                        st.success("✅ Produto encontrado!")
                        try:
                            produto_data = response.json()
                            st.json(produto_data)
                        except:
                            st.code(response.text, language="json")
                    elif response.status_code == 401:
                        st.error("❌ Erro 401 - Token inválido ou expirado")
                        st.warning("Renove o token executando: `python renovar_token.py`")
                        try:
                            erro = response.json()
                            st.json(erro)
                        except:
                            st.code(response.text)
                    else:
                        st.error(f"❌ Erro {response.status_code}")
                        try:
                            erro = response.json()
                            st.json(erro)
                        except:
                            st.code(response.text)
                            
                except Exception as e:
                    st.error(f"❌ Erro na requisição: {str(e)}")
        else:
            st.warning("⚠️ Digite um código de produto")

'''