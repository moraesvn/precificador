import os
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.constants import PROVIDER_TINY
from backend.repositories.oauth_connection_repository import OAuthConnectionRepository
from backend.services.oauth_tiny_service import (
    calculate_expires_at,
    normalize_company_code,
    refresh_tiny_tokens,
)


def ensure_internal_token(x_internal_token: str | None) -> None:
    """
    Valida o token interno usado por jobs/serviços internos para chamar
    endpoints protegidos de integração.
    """
    configured = os.getenv("INTERNAL_JOB_TOKEN", "").strip()
    if not configured:
        raise HTTPException(
            status_code=500,
            detail="Variavel INTERNAL_JOB_TOKEN nao configurada.",
        )
    if x_internal_token != configured:
        raise HTTPException(status_code=401, detail="Token interno invalido.")


def get_tiny_access_token_with_optional_refresh(
    db: Session,
    company_code: str,
    x_internal_token: str | None,
) -> str:
    """
    Obtém o access token do Tiny para a empresa informada e, se estiver
    expirado, tenta fazer refresh automaticamente.
    """
    ensure_internal_token(x_internal_token)

    try:
        normalized = normalize_company_code(company_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = OAuthConnectionRepository(db)
    connection = repo.get_by_company_and_provider(
        company_code=normalized,
        provider=PROVIDER_TINY,
    )
    if connection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhuma conexao Tiny salva para a empresa {normalized}. "
            "Conclua o OAuth em /oauth/tiny/start antes.",
        )

    now = datetime.now(UTC)
    expires_at = connection.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    expired = expires_at is not None and expires_at <= now
    if expired and not connection.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Access token Tiny expirado e sem refresh token. Execute POST /oauth/tiny/refresh.",
        )
    if expired and connection.refresh_token:
        try:
            token_data = refresh_tiny_tokens(
                company_code=normalized,
                refresh_token=connection.refresh_token,
            )
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        connection = repo.upsert_connection_tokens(
            company_code=normalized,
            provider=PROVIDER_TINY,
            access_token=str(token_data["access_token"]),
            refresh_token=str(token_data["refresh_token"])
            if token_data.get("refresh_token")
            else connection.refresh_token,
            token_type=str(token_data["token_type"]) if token_data.get("token_type") else connection.token_type,
            scope=str(token_data["scope"]) if token_data.get("scope") else connection.scope,
            expires_at=calculate_expires_at(token_data),
            external_account_id=connection.external_account_id,
        )

    return connection.access_token
