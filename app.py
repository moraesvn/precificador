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

