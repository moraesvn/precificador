import base64
import hashlib
import os
import secrets
from urllib.parse import urlencode

from backend.constants import PROVIDER_ML, SUPPORTED_COMPANIES
from backend.constants.integrations import CompanyCode, Provider

DEFAULT_ML_AUTH_URL = "https://auth.mercadolivre.com.br/authorization"


def normalize_company_code(company_code: str) -> CompanyCode:
    normalized = company_code.upper()
    if normalized not in SUPPORTED_COMPANIES:
        supported = ", ".join(SUPPORTED_COMPANIES)
        raise ValueError(
            f"Company code invalido: {company_code}. Valores permitidos: {supported}"
        )
    return normalized  # type: ignore[return-value]


def build_ml_oauth_state(company_code: str) -> str:
    normalized_company_code = normalize_company_code(company_code)
    nonce = secrets.token_urlsafe(24)
    return f"company:{normalized_company_code}|provider:{PROVIDER_ML}|nonce:{nonce}"


def parse_ml_oauth_state(state: str) -> tuple[CompanyCode, Provider]:
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

    if provider != PROVIDER_ML:
        raise ValueError("State invalido: provider diferente de ml.")

    return normalized_company_code, provider


def generate_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    challenge_digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


def build_ml_auth_url(
    company_code: str,
    state: str,
    code_challenge: str,
) -> str:
    normalized_company_code = normalize_company_code(company_code)
    client_id = _require_env_value(normalized_company_code, "CLIENT_ID")
    redirect_uri = _require_env_value(normalized_company_code, "REDIRECT_URI")
    auth_url = os.getenv(_env_key(normalized_company_code, "AUTH_URL"), DEFAULT_ML_AUTH_URL).strip()

    query_params = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{auth_url}?{query_params}"


def _env_key(company_code: CompanyCode, field: str) -> str:
    return f"{company_code}_ML_{field}"


def _require_env_value(company_code: CompanyCode, field: str) -> str:
    key = _env_key(company_code, field)
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"Variavel de ambiente obrigatoria ausente: {key}")
    return value
