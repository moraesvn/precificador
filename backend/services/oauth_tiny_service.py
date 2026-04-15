import os
from urllib.parse import urlencode

from backend.constants import SUPPORTED_COMPANIES
from backend.constants.integrations import CompanyCode

TINY_AUTH_BASE_URL = (
    "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth"
)


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
    return f"company:{normalized_company_code}|provider:tiny"
