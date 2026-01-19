import streamlit as st

st.set_page_config(page_title="Callback Tiny V3", page_icon="🔐")

st.title('Callback Tiny')
st.write("Deve existir `code` e `state` na URL.")

params = st.query_params  # Streamlit Cloud já traz os params
st.json(dict(params))
