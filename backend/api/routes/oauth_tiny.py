from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.constants import PROVIDER_TINY
from backend.repositories.oauth_connection_repository import OAuthConnectionRepository
from backend.services.oauth_tiny_service import (
    build_tiny_auth_url,
    build_tiny_oauth_state,
    calculate_expires_at,
    exchange_code_for_tiny_tokens,
    parse_tiny_oauth_state,
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
