"""Chamadas HTTP à API pública do Tiny (Olist ERP v3), separadas do fluxo OAuth."""

from json import JSONDecodeError, loads
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Base oficial da API v3 (mesmo path descrito na documentação OpenAPI).
TINY_ERP_PUBLIC_API_V3_BASE = "https://api.tiny.com.br/public-api/v3"


def _tiny_get(access_token: str, resource_path: str, params: dict[str, str | int]) -> dict[str, Any]:
    """
    Executa uma requisição GET para a API pública v3 do Tiny e retorna o JSON
    já desserializado.
    """
    query = urlencode(params)
    url = f"{TINY_ERP_PUBLIC_API_V3_BASE}/{resource_path}?{query}"

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
            f"Tiny API retornou status {exc.code} no recurso '{resource_path}'. Body: {error_body}"
        ) from exc
    except URLError as exc:
        raise ValueError(f"Erro de conexao com a API do Tiny: {exc.reason}") from exc

    try:
        return loads(body)
    except JSONDecodeError as exc:
        raise ValueError("Resposta da API do Tiny nao e JSON valido.") from exc


def listar_produtos(
    access_token: str,
    *,
    data_alteracao: str,
    limit: int = 100,
    offset: int = 0,
    nome: str | None = None,
    codigo: str | None = None,
    situacao: str | None = None,
    id_lista_preco: int | None = None,
) -> dict[str, Any]:
    """
    GET /produtos com filtro principal por dataAlteracao (formato sugerido pela API:
    'YYYY-MM-DD HH:MM:SS').
    """
    params: dict[str, str | int] = {
        "dataAlteracao": data_alteracao,
        "limit": limit,
        "offset": offset,
    }
    if nome:
        params["nome"] = nome
    if codigo:
        params["codigo"] = codigo
    if situacao:
        params["situacao"] = situacao
    if id_lista_preco is not None:
        params["idListaPreco"] = id_lista_preco

    return _tiny_get(access_token, "produtos", params)


def listar_ordens_compra(
    access_token: str,
    *,
    data_inicial: str,
    data_final: str,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    GET /ordens-compra com filtros por intervalo de cadastro/data no Tiny.

    O Tiny utiliza os parâmetros `dataInicial` e `dataFinal` para o intervalo
    solicitado.
    """
    params: dict[str, str | int] = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "limit": limit,
        "offset": offset,
    }
    return _tiny_get(access_token, "ordem-compra", params)
