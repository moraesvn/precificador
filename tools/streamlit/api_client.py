from typing import Any

import httpx

from config import get_api_base_url, get_internal_token


def _headers() -> dict[str, str]:
    return {"X-Internal-Token": get_internal_token()}


def _url(path: str) -> str:
    base = get_api_base_url()
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> httpx.Response:
    with httpx.Client(timeout=timeout) as client:
        return client.request(
            method,
            _url(path),
            headers=_headers(),
            params=params,
        )


def get_health() -> httpx.Response:
    return request("GET", "/health")


def get_tiny_produtos(params: dict[str, Any]) -> httpx.Response:
    return request("GET", "/tiny/produtos", params=params)


def get_tiny_ordens_compra(params: dict[str, Any]) -> httpx.Response:
    return request("GET", "/tiny/ordens-compra", params=params)


def post_tiny_refresh(company: str) -> httpx.Response:
    return request("POST", "/oauth/tiny/refresh", params={"company": company})


def get_ml_precos(item_id: str, params: dict[str, Any]) -> httpx.Response:
    return request("GET", f"/ml/items/{item_id}/prices", params=params)


def get_ml_sale_price(item_id: str, params: dict[str, Any]) -> httpx.Response:
    return request("GET", f"/ml/items/{item_id}/sale_price", params=params)


def post_ml_refresh(company: str) -> httpx.Response:
    return request("POST", "/oauth/ml/refresh", params={"company": company})


def get_ml_me(params: dict[str, Any]) -> httpx.Response:
    return request("GET", "/ml/me", params=params)


def get_ml_items_search(params: dict[str, Any]) -> httpx.Response:
    return request("GET", "/ml/items/search", params=params)


def get_ml_items_scan(params: dict[str, Any]) -> httpx.Response:
    return request("GET", "/ml/items/scan", params=params, timeout=120.0)


def get_ml_item(item_id: str, params: dict[str, Any]) -> httpx.Response:
    return request("GET", f"/ml/items/{item_id}", params=params)


def post_ml_catalog_sync(company: str) -> httpx.Response:
    return request("POST", "/ml/catalog-sync", params={"company": company})


def get_ml_catalog_sync(run_id: int, company: str) -> httpx.Response:
    return request("GET", f"/ml/catalog-sync/{run_id}", params={"company": company})


def get_ml_sku_map(params: dict[str, Any]) -> httpx.Response:
    return request("GET", "/ml/sku-map", params=params)
