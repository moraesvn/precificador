import streamlit as st

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
    
    st.info("""
    **Próximos passos:**
    1. Copie o código acima
    2. Adicione no seu arquivo `.env`:
       ```
       TINY_AUTHORIZATION_CODE=seu_codigo_aqui
       ```
    3. Execute `python teste.py` para obter o access token
    
    ⚠️ **Importante:** O código expira rapidamente (alguns minutos)!
    """)
    
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
