import base64
import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from json import JSONDecodeError, loads
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.constants import PROVIDER_ML, SUPPORTED_COMPANIES
from backend.constants.integrations import CompanyCode, Provider

DEFAULT_ML_AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
DEFAULT_ML_TOKEN_URL = "https://api.mercadolibre.com/oauth/token"


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


def exchange_code_for_ml_tokens(
    company_code: CompanyCode,
    code: str,
    code_verifier: str,
) -> dict[str, str | int]:
    client_id = _require_env_value(company_code, "CLIENT_ID")
    client_secret = _require_env_value(company_code, "CLIENT_SECRET")
    redirect_uri = _require_env_value(company_code, "REDIRECT_URI")
    token_url = os.getenv(_env_key(company_code, "TOKEN_URL"), DEFAULT_ML_TOKEN_URL).strip()

    token_data = _post_ml_token_request(
        token_url=token_url,
        payload_data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
        action_label="trocar code por token",
    )

    return _validate_token_data(token_data, "troca de code")


def calculate_expires_at(token_data: dict[str, str | int]) -> datetime | None:
    expires_in = token_data.get("expires_in")
    if expires_in is None:
        return None

    try:
        seconds = int(expires_in)
    except (TypeError, ValueError):
        return None

    return datetime.now(UTC) + timedelta(seconds=seconds)


def _env_key(company_code: CompanyCode, field: str) -> str:
    return f"{company_code}_ML_{field}"


def _require_env_value(company_code: CompanyCode, field: str) -> str:
    key = _env_key(company_code, field)
    value = os.getenv(key, "").strip()
    if not value:
        raise ValueError(f"Variavel de ambiente obrigatoria ausente: {key}")
    return value


def _post_ml_token_request(
    token_url: str,
    payload_data: dict[str, str],
    action_label: str,
) -> dict[str, Any]:
    payload = urlencode(payload_data).encode("utf-8")

    request = Request(
        token_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded", "accept": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(
            f"Falha ao {action_label} no Mercado Livre. Status {exc.code}. Body: {error_body}"
        ) from exc
    except URLError as exc:
        raise ValueError(
            f"Erro de conexao ao token endpoint do Mercado Livre: {exc.reason}"
        ) from exc

    try:
        return loads(body)
    except JSONDecodeError as exc:
        raise ValueError(f"Resposta invalida do Mercado Livre ao {action_label}.") from exc


def _validate_token_data(
    token_data: dict[str, Any],
    context_label: str,
) -> dict[str, str | int]:
    if "access_token" not in token_data:
        raise ValueError(f"Resposta do Mercado Livre sem access_token na {context_label}.")
    return token_data
