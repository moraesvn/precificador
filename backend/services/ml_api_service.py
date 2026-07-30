"""Chamadas HTTP à API do Mercado Livre, separadas do fluxo OAuth."""

from json import JSONDecodeError, loads
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ML_API_BASE = "https://api.mercadolibre.com"


def _ml_get(
    access_token: str,
    resource_path: str,
    params: dict[str, str | int] | None = None,
) -> Any:
    """Executa GET na API do Mercado Livre e retorna o JSON desserializado."""
    path = resource_path.lstrip("/")
    url = f"{ML_API_BASE}/{path}"
    if params:
        url = f"{url}?{urlencode(params)}"

    request = Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(
            f"Mercado Livre API retornou status {exc.code} em '{resource_path}'. Body: {error_body}"
        ) from exc
    except URLError as exc:
        raise ValueError(f"Erro de conexao com a API do Mercado Livre: {exc.reason}") from exc

    try:
        return loads(body)
    except JSONDecodeError as exc:
        raise ValueError("Resposta da API do Mercado Livre nao e JSON valido.") from exc


def obter_item(
    access_token: str,
    item_id: str,
    *,
    include_attributes: str | None = "all",
) -> dict[str, Any]:
    """
    GET /items/{item_id} — detalhe do anúncio.

    Com include_attributes=all a resposta inclui SELLER_SKU e attributes das variações.
    """
    item_id = item_id.strip()
    if not item_id:
        raise ValueError("item_id obrigatorio.")

    params: dict[str, str] = {}
    attributes_value = (include_attributes or "").strip()
    if attributes_value:
        params["include_attributes"] = attributes_value

    return _ml_get(access_token, f"items/{item_id}", params or None)


def obter_itens_em_lote(
    access_token: str,
    item_ids: list[str],
    *,
    include_attributes: str | None = "all",
) -> list[dict[str, Any]]:
    """
    GET /items?ids=... — detalhes de até 20 anúncios em uma única chamada.

    A API retorna uma lista de envelopes com code e body para cada ITEM_ID.
    """
    normalized_ids = [item_id.strip() for item_id in item_ids if item_id.strip()]
    if not normalized_ids:
        raise ValueError("Informe ao menos um item_id.")
    if len(normalized_ids) > 20:
        raise ValueError("A consulta em lote aceita no maximo 20 item_ids.")

    params: dict[str, str] = {"ids": ",".join(normalized_ids)}
    attributes_value = (include_attributes or "").strip()
    if attributes_value:
        params["include_attributes"] = attributes_value

    response = _ml_get(access_token, "items", params)
    if not isinstance(response, list):
        raise ValueError("Resposta invalida do multiget de itens do Mercado Livre.")
    return response


def obter_precos_item(access_token: str, item_id: str) -> dict[str, Any]:
    """
    GET /items/{item_id}/prices — todos os preços (standard e promotion) do anúncio.
    """
    item_id = item_id.strip()
    if not item_id:
        raise ValueError("item_id obrigatorio.")
    return _ml_get(access_token, f"items/{item_id}/prices")


def obter_preco_venda(
    access_token: str,
    item_id: str,
    *,
    context: str | None = None,
) -> dict[str, Any]:
    """
    GET /items/{item_id}/sale_price — preço de venda vencedor para o contexto informado.

    context: valores separados por vírgula, ex. channel_marketplace,buyer_loyalty_3
    """
    item_id = item_id.strip()
    if not item_id:
        raise ValueError("item_id obrigatorio.")

    params: dict[str, str] = {}
    context_value = (context or "").strip()
    if context_value:
        params["context"] = context_value

    return _ml_get(access_token, f"items/{item_id}/sale_price", params or None)


def obter_usuario_autenticado(access_token: str) -> dict[str, Any]:
    """GET /users/me — dados do vendedor autenticado pelo token."""
    return _ml_get(access_token, "users/me")


def buscar_itens_vendedor(
    access_token: str,
    user_id: str,
    *,
    status: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """
    GET /users/{user_id}/items/search — anúncios do vendedor sem informar item_id.
    """
    user_id = user_id.strip()
    if not user_id:
        raise ValueError("user_id obrigatorio.")

    params: dict[str, str | int] = {
        "limit": limit,
        "offset": offset,
    }
    status_value = (status or "").strip()
    if status_value:
        params["status"] = status_value

    return _ml_get(access_token, f"users/{user_id}/items/search", params)


def buscar_todos_itens_ativos_vendedor(
    access_token: str,
    user_id: str,
    *,
    tags: str | None = None,
    limit_per_page: int = 100,
) -> dict[str, Any]:
    """
    Lista anúncios ativos do vendedor usando search_type=scan.

    O scan é necessário para contas com mais de 1.000 anúncios. As páginas são
    percorridas até o Mercado Livre retornar results vazio ou nulo.

    tags: filtro opcional (ex.: catalog_boost) enviado na primeira página do scan.
    """
    user_id = user_id.strip()
    if not user_id:
        raise ValueError("user_id obrigatorio.")
    if not 1 <= limit_per_page <= 100:
        raise ValueError("limit_per_page deve estar entre 1 e 100.")

    resource_path = f"users/{user_id}/items/search"
    params: dict[str, str | int] = {
        "search_type": "scan",
        "status": "active",
        "limit": limit_per_page,
    }
    tags_value = (tags or "").strip()
    if tags_value:
        params["tags"] = tags_value

    item_ids: list[str] = []
    seen_item_ids: set[str] = set()
    pages = 0

    while True:
        response = _ml_get(access_token, resource_path, params)
        pages += 1

        results = response.get("results")
        if not results:
            break
        if not isinstance(results, list):
            raise ValueError("Resposta do scan sem lista valida em results.")

        for item_id in results:
            normalized_item_id = str(item_id).strip()
            if normalized_item_id and normalized_item_id not in seen_item_ids:
                seen_item_ids.add(normalized_item_id)
                item_ids.append(normalized_item_id)

        response_scroll_id = str(response.get("scroll_id") or "").strip()
        if not response_scroll_id:
            raise ValueError("Mercado Livre nao retornou scroll_id para continuar o scan.")

        params = {
            "search_type": "scan",
            "scroll_id": response_scroll_id,
            "limit": limit_per_page,
        }

    return {
        "seller_id": user_id,
        "status": "active",
        "tags": tags_value or None,
        "total": len(item_ids),
        "pages": pages,
        "results": item_ids,
    }


def buscar_itens_catalog_boost_ativos(
    access_token: str,
    user_id: str,
    *,
    limit_per_page: int = 100,
) -> dict[str, Any]:
    """Lista anúncios ativos com tag catalog_boost (opt-in automático do ML)."""
    return buscar_todos_itens_ativos_vendedor(
        access_token,
        user_id,
        tags="catalog_boost",
        limit_per_page=limit_per_page,
    )

