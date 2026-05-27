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
