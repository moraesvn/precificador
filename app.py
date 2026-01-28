import streamlit as st
from services.tiny_service import TinyService
from datetime import datetime

st.set_page_config(page_title="Teste API Tiny", page_icon="🧪")

st.title("🧪 Teste - Listar Produtos API Tiny")

# Campo para data de alteração
data_alteracao = st.date_input(
    "Produtos atualizados a partir de:",
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
            # Extrair lista de produtos da resposta (estrutura: {"itens": [...]})
            produtos = []
            if isinstance(resultado, dict):
                produtos = resultado.get("itens", [])
            elif isinstance(resultado, list):
                produtos = resultado
            
            if produtos and len(produtos) > 0:
                st.success(f"✅ {len(produtos)} produto(s) encontrado(s)!")
                
                # Preparar dados para a tabela
                dados_tabela = []
                for produto in produtos:
                    # Extrair preços do objeto precos
                    precos = produto.get("precos", {})
                    
                    dados_tabela.append({
                        "sku": produto.get("sku", ""),
                        "descricao": produto.get("descricao", ""),
                        "gtin": produto.get("gtin", ""),
                        "preco": precos.get("preco", ""),
                        "precoPromocional": precos.get("precoPromocional", ""),
                        "precoCusto": precos.get("precoCusto", ""),
                        "precoCustoMedio": precos.get("precoCustoMedio", "")
                    })
                
                # Exibir tabela
                st.table(dados_tabela)
            else:
                st.warning("⚠️ Nenhum produto encontrado na resposta")
                st.json(resultado)
        else:
            st.error("❌ Erro ao buscar produtos ou nenhum produto encontrado")