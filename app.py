import streamlit as st
from services.tiny_service import TinyService
from datetime import datetime

st.set_page_config(page_title="Teste API Tiny", page_icon="🧪")

st.title("🧪 Teste - Listar Produtos API Tiny")

# Campo para data de alteração
data_alteracao = st.date_input(
    "Data de Alteração (opcional)",
    value=None,
    help="Filtra produtos modificados a partir desta data"
)

# Botão para buscar produtos
if st.button("🔍 Buscar Produtos", type="primary"):
    with st.spinner("Buscando produtos..."):
        service = TinyService()
        
        # Converter data para string se fornecida
        data_str = None
        if data_alteracao:
            data_str = data_alteracao.strftime("%Y-%m-%d")
        
        # Chamar a função
        resultado = service.listar_produtos(dataAlteracao=data_str)
        
        if resultado:
            st.success("✅ Produtos encontrados!")
            st.json(resultado)
        else:
            st.error("❌ Erro ao buscar produtos ou nenhum produto encontrado")