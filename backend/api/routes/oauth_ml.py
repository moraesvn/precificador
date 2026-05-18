import os
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.constants import PROVIDER_ML
from backend.repositories.oauth_connection_repository import OAuthConnectionRepository
from backend.repositories.oauth_state_repository import OAuthStateRepository
from backend.services.oauth_ml_service import (
    build_ml_auth_url,
    build_ml_oauth_state,
    calculate_expires_at,
    exchange_code_for_ml_tokens,
    generate_pkce_pair,
    normalize_company_code,
    parse_ml_oauth_state,
    refresh_ml_tokens,
)


router = APIRouter(prefix="/oauth/ml", tags=["oauth-ml"])


@router.get("/start")
def ml_start(
    company: str = Query(default="SP"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        company_code = normalize_company_code(company)
        state = build_ml_oauth_state(company_code)
        code_verifier, code_challenge = generate_pkce_pair()
        auth_url = build_ml_auth_url(company_code, state, code_challenge)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    oauth_state_repository = OAuthStateRepository(db)
    oauth_state_repository.create_state(
        state=state,
        company_code=company_code,
        provider=PROVIDER_ML,
        code_verifier=code_verifier,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )

    return {
        "provider": PROVIDER_ML,
        "company_code": company_code,
        "state": state,
        "code_challenge_method": "S256",
        "auth_url": auth_url,
    }


@router.get("/callback")
@router.get("/callback/")
def ml_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Mercado Livre retornou erro de autorizacao: {error}",
        )

    if not code:
        raise HTTPException(status_code=400, detail="Parametro code ausente no callback.")

    if not state:
        raise HTTPException(status_code=400, detail="Parametro state ausente no callback.")

    oauth_state_repository = OAuthStateRepository(db)
    state_record = oauth_state_repository.get_by_state(state)

    if state_record is None:
        raise HTTPException(status_code=400, detail="State invalido ou nao encontrado.")

    if state_record.used_at is not None:
        raise HTTPException(status_code=400, detail="State ja utilizado anteriormente.")

    now = datetime.now(UTC)
    if state_record.expires_at < now:
        raise HTTPException(status_code=400, detail="State expirado. Reinicie o fluxo de login.")

    try:
        company_code, provider = parse_ml_oauth_state(state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if state_record.company_code != company_code or state_record.provider != provider:
        raise HTTPException(status_code=400, detail="State inconsistente com os dados persistidos.")

    try:
        token_data = exchange_code_for_ml_tokens(
            company_code=company_code,
            code=code,
            code_verifier=state_record.code_verifier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connection_repository = OAuthConnectionRepository(db)
    saved_connection = connection_repository.upsert_connection_tokens(
        company_code=company_code,
        provider=provider,
        access_token=str(token_data["access_token"]),
        refresh_token=str(token_data["refresh_token"]) if token_data.get("refresh_token") else None,
        token_type=str(token_data["token_type"]) if token_data.get("token_type") else None,
        scope=str(token_data["scope"]) if token_data.get("scope") else None,
        expires_at=calculate_expires_at(token_data),
        external_account_id=str(token_data["user_id"]) if token_data.get("user_id") else None,
    )

    oauth_state_repository.mark_as_used(state_record, now)

    return {
        "provider": provider,
        "company_code": company_code,
        "message": "Autenticacao Mercado Livre concluida e tokens salvos com sucesso.",
        "connection_id": str(saved_connection.id),
        "state": state,
        "error": None,
        "code": None,
        "access_token_saved": "true",
        "refresh_token_saved": "true" if saved_connection.refresh_token else "false",
        "expires_at": saved_connection.expires_at.isoformat() if saved_connection.expires_at else None,
    }


@router.post("/refresh")
def ml_refresh(
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
        provider=PROVIDER_ML,
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conexao OAuth nao encontrada para {company_code} + {PROVIDER_ML}.",
        )

    if not connection.refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Refresh token ausente para a conexao informada.",
        )

    try:
        token_data = refresh_ml_tokens(
            company_code=company_code,
            refresh_token=connection.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved_connection = repository.upsert_connection_tokens(
        company_code=company_code,
        provider=PROVIDER_ML,
        access_token=str(token_data["access_token"]),
        refresh_token=str(token_data["refresh_token"]) if token_data.get("refresh_token") else connection.refresh_token,
        token_type=str(token_data["token_type"]) if token_data.get("token_type") else connection.token_type,
        scope=str(token_data["scope"]) if token_data.get("scope") else connection.scope,
        expires_at=calculate_expires_at(token_data),
        external_account_id=str(token_data["user_id"]) if token_data.get("user_id") else connection.external_account_id,
    )

    return {
        "provider": PROVIDER_ML,
        "company_code": company_code,
        "message": "Refresh do token Mercado Livre executado com sucesso.",
        "connection_id": str(saved_connection.id),
        "access_token_saved": "true",
        "refresh_token_saved": "true" if saved_connection.refresh_token else "false",
        "expires_at": saved_connection.expires_at.isoformat() if saved_connection.expires_at else None,
    }
