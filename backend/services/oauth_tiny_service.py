import os
from datetime import UTC, datetime, timedelta
from json import JSONDecodeError, loads
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.constants import PROVIDER_TINY, SUPPORTED_COMPANIES
from backend.constants.integrations import CompanyCode, Provider

TINY_AUTH_BASE_URL = (
    "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth"
)
TINY_TOKEN_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token"


def _env_key(company_code: CompanyCode, field: str) -> str:
    return f"{company_code}_TINY_{field}"


def _require_env_value(company_code: CompanyCode, field: str) -> str:
    key = _env_key(company_code, field)
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"Variavel de ambiente obrigatoria ausente: {key}")
    return value


def normalize_company_code(company_code: str) -> CompanyCode:
    normalized = company_code.upper()
    if normalized not in SUPPORTED_COMPANIES:
        supported = ", ".join(SUPPORTED_COMPANIES)
        raise ValueError(
            f"Company code invalido: {company_code}. Valores permitidos: {supported}"
        )
    return normalized  # type: ignore[return-value]


def build_tiny_auth_url(company_code: str, state: str) -> str:
    normalized_company_code = normalize_company_code(company_code)

    client_id = _require_env_value(normalized_company_code, "CLIENT_ID")
    redirect_uri = _require_env_value(normalized_company_code, "REDIRECT_URI")

    query_params = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid",
            "response_type": "code",
            "state": state,
        }
    )
    return f"{TINY_AUTH_BASE_URL}?{query_params}"


def build_tiny_oauth_state(company_code: str) -> str:
    normalized_company_code = normalize_company_code(company_code)
    return f"company:{normalized_company_code}|provider:{PROVIDER_TINY}"


def parse_tiny_oauth_state(state: str) -> tuple[CompanyCode, Provider]:
    parts = state.split("|")
    values: dict[str, str] = {}
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        values[key] = value

    company_code = values.get("company")
    provider = values.get("provider")

    if not company_code:
        raise ValueError("State invalido: company ausente.")

    normalized_company_code = normalize_company_code(company_code)

    if provider != PROVIDER_TINY:
        raise ValueError("State invalido: provider diferente de tiny.")

    return normalized_company_code, provider


def exchange_code_for_tiny_tokens(company_code: CompanyCode, code: str) -> dict[str, str | int]:
    client_id = _require_env_value(company_code, "CLIENT_ID")
    client_secret = _require_env_value(company_code, "CLIENT_SECRET")
    redirect_uri = _require_env_value(company_code, "REDIRECT_URI")

    payload = urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")

    request = Request(
        TINY_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(
            f"Falha ao trocar code por token no Tiny. Status {exc.code}. Body: {error_body}"
        ) from exc
    except URLError as exc:
        raise ValueError(f"Erro de conexao ao token endpoint do Tiny: {exc.reason}") from exc

    try:
        token_data = loads(body)
    except JSONDecodeError as exc:
        raise ValueError("Resposta invalida do Tiny ao trocar token.") from exc

    if "access_token" not in token_data:
        raise ValueError("Resposta do Tiny sem access_token.")

    return token_data


def calculate_expires_at(token_data: dict[str, str | int]) -> datetime | None:
    expires_in = token_data.get("expires_in")
    if expires_in is None:
        return None

    try:
        seconds = int(expires_in)
    except (TypeError, ValueError):
        return None

    return datetime.now(UTC) + timedelta(seconds=seconds)
