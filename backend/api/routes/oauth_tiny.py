import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.constants import PROVIDER_TINY
from backend.repositories.oauth_connection_repository import OAuthConnectionRepository
from backend.services.oauth_tiny_service import (
    build_tiny_auth_url,
    build_tiny_oauth_state,
    calculate_expires_at,
    exchange_code_for_tiny_tokens,
    normalize_company_code,
    parse_tiny_oauth_state,
    refresh_tiny_tokens,
)


router = APIRouter(prefix="/oauth/tiny", tags=["oauth-tiny"])


@router.get("/start")
def tiny_start(company: str = Query(default="SP")) -> dict[str, str]:
    try:
        state = build_tiny_oauth_state(company)
        auth_url = build_tiny_auth_url(company, state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "provider": PROVIDER_TINY,
        "company_code": company.upper(),
        "auth_url": auth_url,
        "state": state,
    }


@router.get("/callback")
def tiny_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Tiny retornou erro de autorizacao: {error}",
        )

    if not code:
        raise HTTPException(status_code=400, detail="Parametro code ausente no callback.")

    if not state:
        raise HTTPException(status_code=400, detail="Parametro state ausente no callback.")

    try:
        company_code, provider = parse_tiny_oauth_state(state)
        token_data = exchange_code_for_tiny_tokens(company_code, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = OAuthConnectionRepository(db)
    saved_connection = repository.upsert_connection_tokens(
        company_code=company_code,
        provider=provider,
        access_token=str(token_data["access_token"]),
        refresh_token=str(token_data["refresh_token"]) if token_data.get("refresh_token") else None,
        token_type=str(token_data["token_type"]) if token_data.get("token_type") else None,
        scope=str(token_data["scope"]) if token_data.get("scope") else None,
        expires_at=calculate_expires_at(token_data),
    )

    return {
        "provider": provider,
        "company_code": company_code,
        "message": "Autenticacao Tiny concluida e tokens salvos com sucesso.",
        "connection_id": str(saved_connection.id),
        "state": state,
        "error": None,
        "code": None,
        "access_token_saved": "true",
        "refresh_token_saved": "true" if saved_connection.refresh_token else "false",
        "expires_at": saved_connection.expires_at.isoformat() if saved_connection.expires_at else None,
    }


@router.get("/callback/")
def tiny_callback_with_trailing_slash(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    return tiny_callback(
        code=code,
        state=state,
        error=error,
        db=db,
    )


@router.post("/refresh")
def tiny_refresh(
    company: str = Query(default="SP"),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    configured_internal_token = os.getenv("INTERNAL_JOB_TOKEN", "").strip()
    if not configured_internal_token:
        raise HTTPException(
            status_code=500,
            detail="Variavel INTERNAL_JOB_TOKEN nao configurada.",
        )

    if x_internal_token != configured_internal_token:
        raise HTTPException(status_code=401, detail="Token interno invalido.")

    try:
        company_code = normalize_company_code(company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repository = OAuthConnectionRepository(db)
    connection = repository.get_by_company_and_provider(
        company_code=company_code,
        provider=PROVIDER_TINY,
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conexao OAuth nao encontrada para {company_code} + {PROVIDER_TINY}.",
        )

    if not connection.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Refresh token ausente para a conexao informada.",
        )

    try:
        token_data = refresh_tiny_tokens(
            company_code=company_code,
            refresh_token=connection.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved_connection = repository.upsert_connection_tokens(
        company_code=company_code,
        provider=PROVIDER_TINY,
        access_token=str(token_data["access_token"]),
        refresh_token=str(token_data["refresh_token"]) if token_data.get("refresh_token") else connection.refresh_token,
        token_type=str(token_data["token_type"]) if token_data.get("token_type") else connection.token_type,
        scope=str(token_data["scope"]) if token_data.get("scope") else connection.scope,
        expires_at=calculate_expires_at(token_data),
        external_account_id=connection.external_account_id,
    )

    return {
        "provider": PROVIDER_TINY,
        "company_code": company_code,
        "message": "Refresh do token Tiny executado com sucesso.",
        "connection_id": str(saved_connection.id),
        "access_token_saved": "true",
        "refresh_token_saved": "true" if saved_connection.refresh_token else "false",
        "expires_at": saved_connection.expires_at.isoformat() if saved_connection.expires_at else None,
    }
