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
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
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
