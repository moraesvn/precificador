"""Console local para testar a API Precificador em producao (nao vai para a VPS)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import streamlit as st

from api_client import (
    get_health,
    get_ml_items_search,
    get_ml_me,
    get_ml_precos,
    get_ml_sale_price,
    get_tiny_ordens_compra,
    get_tiny_produtos,
    post_ml_refresh,
    post_tiny_refresh,
)
from config import config_ok, get_api_base_url, get_internal_token

st.set_page_config(page_title="Precificador — testes API", layout="wide")

LIST_KEYS = ("itens", "produtos", "data", "results", "registros")


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _show_response(response) -> None:
    st.caption(f"HTTP {response.status_code}")
    try:
        body = response.json()
    except Exception:
        st.code(response.text or "(corpo vazio)")
        return
    if not response.is_success:
        detail = body.get("detail", body) if isinstance(body, dict) else body
        st.error(detail)
        with st.expander("Resposta completa"):
            st.json(body)
        return
    st.json(body)


def _sidebar_status() -> bool:
    ok, message = config_ok()
    st.sidebar.title("Precificador")
    st.sidebar.caption("Streamlit local — API em producao")
    st.sidebar.markdown(f"**Base:** `{get_api_base_url()}`")
    if ok:
        st.sidebar.success(f"Token: `{_mask_token(get_internal_token())}`")
    else:
        st.sidebar.error(message)
        st.sidebar.info(
            "Crie `tools/streamlit/.env` a partir de `.env.example` "
            "com `API_BASE_URL` e `INTERNAL_JOB_TOKEN`."
        )
    st.sidebar.link_button("OpenAPI /docs", f"{get_api_base_url()}/docs")
    return ok


def _tab_health() -> None:
    st.subheader("Health")
    if st.button("GET /health", key="btn_health"):
        with st.spinner("Chamando API..."):
            response = get_health()
        _show_response(response)


def _tab_produtos() -> None:
    st.subheader("Tiny — listar produtos")
    st.caption("Proxy: `GET /tiny/produtos` (token OAuth fica no servidor)")

    default_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")

    col1, col2, col3 = st.columns(3)
    with col1:
        company = st.selectbox("Empresa", ["SP", "SC"], key="prod_company")
    with col2:
        data_alteracao = st.text_input(
            "data_alteracao",
            value=default_date,
            help="Formato: YYYY-MM-DD HH:MM:SS",
            key="prod_data_alteracao",
        )
    with col3:
        situacao = st.selectbox(
            "Situacao",
            ["(todas)", "A", "I", "E"],
            help="A=Ativo, I=Inativo, E=Excluido",
            key="prod_situacao",
        )

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        limit = st.number_input("limit", min_value=1, max_value=500, value=100, key="prod_limit")
    with col5:
        offset = st.number_input("offset", min_value=0, value=0, key="prod_offset")
    with col6:
        nome = st.text_input("nome (opcional)", key="prod_nome")
    with col7:
        codigo = st.text_input("codigo (opcional)", key="prod_codigo")

    id_lista_preco = st.number_input(
        "id_lista_preco (opcional, 0 = ignorar)",
        min_value=0,
        value=0,
        key="prod_id_lista",
    )

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        buscar = st.button("Buscar produtos", type="primary", key="btn_produtos")
    with btn_col2:
        prev_page = st.button("← Pagina anterior", key="btn_prev")
    with btn_col3:
        next_page = st.button("Proxima pagina →", key="btn_next")

    if "prod_offset_state" not in st.session_state:
        st.session_state.prod_offset_state = int(offset)

    if prev_page:
        st.session_state.prod_offset_state = max(
            0, st.session_state.prod_offset_state - int(limit)
        )
        buscar = True
    if next_page:
        st.session_state.prod_offset_state = st.session_state.prod_offset_state + int(limit)
        buscar = True

    if buscar:
        if not (prev_page or next_page):
            st.session_state.prod_offset_state = int(offset)
        params: dict[str, Any] = {
            "company": company,
            "data_alteracao": data_alteracao.strip(),
            "limit": int(limit),
            "offset": st.session_state.prod_offset_state,
        }
        if situacao != "(todas)":
            params["situacao"] = situacao
        if nome.strip():
            params["nome"] = nome.strip()
        if codigo.strip():
            params["codigo"] = codigo.strip()
        if id_lista_preco > 0:
            params["id_lista_preco"] = int(id_lista_preco)

        if not params["data_alteracao"]:
            st.warning("Informe data_alteracao.")
            return

        with st.spinner("Chamando /tiny/produtos..."):
            response = get_tiny_produtos(params)

        st.session_state.last_produtos_params = params
        st.session_state.last_produtos_response = response

    response = st.session_state.get("last_produtos_response")
    if response is None:
        return

    st.divider()
    st.caption(f"HTTP {response.status_code} | params: `{st.session_state.get('last_produtos_params')}`")

    try:
        body = response.json()
    except Exception:
        st.code(response.text)
        return

    if not response.is_success:
        st.error(body.get("detail", body) if isinstance(body, dict) else body)
        with st.expander("JSON completo"):
            st.json(body)
        return

    rows = _extract_rows(body)
    if rows:
        st.metric("Registros nesta pagina", len(rows))
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma lista reconhecida no JSON (chaves: itens, produtos, data...). Veja o JSON abaixo.")

    with st.expander("JSON bruto"):
        st.json(body)

    st.download_button(
        "Baixar JSON",
        data=json.dumps(body, ensure_ascii=False, indent=2),
        file_name="tiny_produtos.json",
        mime="application/json",
    )


def _tab_ordens_compra() -> None:
    st.subheader("Tiny — listar ordens de compra")
    st.caption("Proxy: `GET /tiny/ordens-compra` (token OAuth fica no servidor)")

    default_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    default_end = datetime.now().strftime("%Y-%m-%d")

    col1, col2, col3 = st.columns(3)
    with col1:
        company = st.selectbox("Empresa", ["SP", "SC"], key="oc_company")
    with col2:
        data_inicial = st.text_input(
            "data_inicial",
            value=default_start,
            help="Formato: YYYY-MM-DD",
            key="oc_data_inicial",
        )
    with col3:
        data_final = st.text_input(
            "data_final",
            value=default_end,
            help="Formato: YYYY-MM-DD",
            key="oc_data_final",
        )

    col4, col5 = st.columns(2)
    with col4:
        limit = st.number_input("limit", min_value=1, max_value=500, value=100, key="oc_limit")
    with col5:
        offset = st.number_input("offset", min_value=0, value=0, key="oc_offset")

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        buscar = st.button("Buscar ordens", type="primary", key="btn_ordens_compra")
    with btn_col2:
        prev_page = st.button("← Pagina anterior", key="btn_oc_prev")
    with btn_col3:
        next_page = st.button("Proxima pagina →", key="btn_oc_next")

    if "oc_offset_state" not in st.session_state:
        st.session_state.oc_offset_state = int(offset)

    if prev_page:
        st.session_state.oc_offset_state = max(0, st.session_state.oc_offset_state - int(limit))
        buscar = True
    if next_page:
        st.session_state.oc_offset_state = st.session_state.oc_offset_state + int(limit)
        buscar = True

    if buscar:
        if not (prev_page or next_page):
            st.session_state.oc_offset_state = int(offset)

        params: dict[str, Any] = {
            "company": company,
            "data_inicial": data_inicial.strip(),
            "data_final": data_final.strip(),
            "limit": int(limit),
            "offset": st.session_state.oc_offset_state,
        }

        if not params["data_inicial"] or not params["data_final"]:
            st.warning("Informe data_inicial e data_final.")
            return

        with st.spinner("Chamando /tiny/ordens-compra..."):
            response = get_tiny_ordens_compra(params)

        st.session_state.last_oc_params = params
        st.session_state.last_oc_response = response

    response = st.session_state.get("last_oc_response")
    if response is None:
        return

    st.divider()
    st.caption(f"HTTP {response.status_code} | params: `{st.session_state.get('last_oc_params')}`")

    try:
        body = response.json()
    except Exception:
        st.code(response.text)
        return

    if not response.is_success:
        st.error(body.get("detail", body) if isinstance(body, dict) else body)
        with st.expander("JSON completo"):
            st.json(body)
        return

    rows = _extract_rows(body)
    if rows:
        st.metric("Registros nesta pagina", len(rows))
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma lista reconhecida no JSON (chaves: itens, produtos, data...). Veja o JSON abaixo.")

    with st.expander("JSON bruto"):
        st.json(body)

    st.download_button(
        "Baixar JSON",
        data=json.dumps(body, ensure_ascii=False, indent=2),
        file_name="tiny_ordens_compra.json",
        mime="application/json",
    )


def _tab_refresh() -> None:
    st.subheader("Tiny — refresh token")
    st.caption("`POST /oauth/tiny/refresh` — util se o access token expirou")
    company = st.selectbox("Empresa", ["SP", "SC"], key="refresh_company")
    if st.button("Executar refresh", key="btn_refresh"):
        with st.spinner("Atualizando tokens..."):
            response = post_tiny_refresh(company)
        _show_response(response)


def _tab_ml_precos() -> None:
    st.subheader("Mercado Livre")
    st.caption("Token OAuth fica no servidor — testes via proxy da API")

    company = st.selectbox("Empresa", ["SP", "SC"], key="ml_company")
    item_id = st.text_input(
        "item_id (para consulta de preços)",
        placeholder="Ex.: MLB1234567890",
        help="Use a aba Conta e anúncios para listar IDs sem digitar manualmente",
        key="ml_item_id",
    )

    sub_conta, sub_precos, sub_sale, sub_refresh = st.tabs(
        ["Conta e anúncios", "Todos os preços", "Preço de venda", "Refresh token"]
    )

    with sub_conta:
        st.caption("`GET /ml/me` e `GET /ml/items/search` — sem informar item_id")

        col_me, col_search = st.columns(2)
        with col_me:
            if st.button("Quem sou eu?", type="primary", key="btn_ml_me"):
                params = {"company": company}
                with st.spinner("Chamando /ml/me..."):
                    response = get_ml_me(params)
                st.session_state.last_ml_me_response = response

        with col_search:
            status = st.selectbox(
                "status",
                ["active", "paused", "closed", "under_review", "inactive"],
                key="ml_search_status",
            )
            limit = st.number_input(
                "limit", min_value=1, max_value=50, value=10, key="ml_search_limit"
            )
            if st.button("Listar meus anúncios", type="primary", key="btn_ml_search"):
                params = {
                    "company": company,
                    "status": status,
                    "limit": int(limit),
                    "offset": 0,
                }
                with st.spinner("Chamando /ml/items/search..."):
                    response = get_ml_items_search(params)
                st.session_state.last_ml_search_response = response
                st.session_state.last_ml_search_params = params

        me_response = st.session_state.get("last_ml_me_response")
        if me_response is not None:
            st.divider()
            st.markdown("**Perfil autenticado**")
            st.caption(f"HTTP {me_response.status_code}")
            try:
                body = me_response.json()
            except Exception:
                st.code(me_response.text)
            elif not me_response.is_success:
                st.error(body.get("detail", body) if isinstance(body, dict) else body)
            elif isinstance(body, dict):
                cols = st.columns(4)
                cols[0].metric("ID", body.get("id", "—"))
                cols[1].metric("Nickname", body.get("nickname", "—"))
                cols[2].metric("Site", body.get("site_id", "—"))
                cols[3].metric("País", body.get("country_id", "—"))
                with st.expander("JSON completo"):
                    st.json(body)

        search_response = st.session_state.get("last_ml_search_response")
        if search_response is not None:
            st.divider()
            st.markdown("**Anúncios**")
            st.caption(
                f"HTTP {search_response.status_code} | "
                f"params: `{st.session_state.get('last_ml_search_params')}`"
            )
            try:
                body = search_response.json()
            except Exception:
                st.code(search_response.text)
            elif not search_response.is_success:
                st.error(body.get("detail", body) if isinstance(body, dict) else body)
                with st.expander("JSON completo"):
                    st.json(body)
            elif isinstance(body, dict):
                results = body.get("results")
                if isinstance(results, list) and results:
                    st.metric("Anúncios nesta página", len(results))
                    rows = [{"item_id": iid} for iid in results]
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    st.info("Copie um item_id da lista para testar na aba de preços.")
                else:
                    st.info("Nenhum anúncio retornado para os filtros informados.")

                paging = body.get("paging")
                if isinstance(paging, dict):
                    st.caption(
                        f"Total: {paging.get('total', '—')} | "
                        f"offset: {paging.get('offset', '—')} | "
                        f"limit: {paging.get('limit', '—')}"
                    )
                with st.expander("JSON bruto"):
                    st.json(body)

    with sub_precos:
        st.caption("`GET /ml/items/{item_id}/prices` — standard e promotion")
        if st.button("Consultar preços", type="primary", key="btn_ml_precos"):
            if not item_id.strip():
                st.warning("Informe o item_id.")
            else:
                params = {"company": company}
                with st.spinner("Chamando /ml/items/.../prices..."):
                    response = get_ml_precos(item_id.strip(), params)
                st.session_state.last_ml_precos_response = response
                st.session_state.last_ml_precos_params = params

        response = st.session_state.get("last_ml_precos_response")
        if response is not None:
            st.divider()
            st.caption(f"HTTP {response.status_code}")
            try:
                body = response.json()
            except Exception:
                st.code(response.text)
                return
            if not response.is_success:
                st.error(body.get("detail", body) if isinstance(body, dict) else body)
                with st.expander("JSON completo"):
                    st.json(body)
                return

            prices = body.get("prices") if isinstance(body, dict) else None
            if isinstance(prices, list) and prices:
                st.metric("Preços retornados", len(prices))
                st.dataframe(pd.DataFrame(prices), use_container_width=True, hide_index=True)
            with st.expander("JSON bruto"):
                st.json(body)

    with sub_sale:
        st.caption("`GET /ml/items/{item_id}/sale_price` — preço vencedor no contexto")
        context = st.text_input(
            "context (opcional)",
            value="channel_marketplace",
            help="Ex.: channel_marketplace,buyer_loyalty_3",
            key="ml_context",
        )
        if st.button("Consultar preço de venda", type="primary", key="btn_ml_sale"):
            if not item_id.strip():
                st.warning("Informe o item_id.")
            else:
                params: dict[str, Any] = {"company": company}
                if context.strip():
                    params["context"] = context.strip()
                with st.spinner("Chamando /ml/items/.../sale_price..."):
                    response = get_ml_sale_price(item_id.strip(), params)
                st.session_state.last_ml_sale_response = response
                st.session_state.last_ml_sale_params = params

        response = st.session_state.get("last_ml_sale_response")
        if response is not None:
            st.divider()
            st.caption(f"HTTP {response.status_code}")
            try:
                body = response.json()
            except Exception:
                st.code(response.text)
                return
            if not response.is_success:
                st.error(body.get("detail", body) if isinstance(body, dict) else body)
                with st.expander("JSON completo"):
                    st.json(body)
                return

            if isinstance(body, dict) and "amount" in body:
                cols = st.columns(3)
                cols[0].metric("Preço de venda", f"{body.get('amount')} {body.get('currency_id', '')}")
                regular = body.get("regular_amount")
                if regular is not None:
                    cols[1].metric("Preço regular", f"{regular} {body.get('currency_id', '')}")
                if body.get("metadata"):
                    cols[2].json(body["metadata"])
            with st.expander("JSON bruto"):
                st.json(body)

    with sub_refresh:
        st.caption("`POST /oauth/ml/refresh` — util se o access token expirou")
        if st.button("Executar refresh ML", key="btn_ml_refresh"):
            with st.spinner("Atualizando tokens..."):
                response = post_ml_refresh(company)
            _show_response(response)


def main() -> None:
    if not _sidebar_status():
        st.title("Configuracao necessaria")
        st.stop()

    st.title("Testes API Precificador")
    tab_health, tab_produtos, tab_ordens_compra, tab_ml, tab_refresh = st.tabs(
        ["Health", "Produtos Tiny", "Ordens de Compra Tiny", "Mercado Livre", "Refresh Tiny"]
    )
    with tab_health:
        _tab_health()
    with tab_produtos:
        _tab_produtos()
    with tab_ordens_compra:
        _tab_ordens_compra()
    with tab_ml:
        _tab_ml_precos()
    with tab_refresh:
        _tab_refresh()


if __name__ == "__main__":
    main()
