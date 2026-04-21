from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.constants import PROVIDER_ML
from backend.repositories.oauth_state_repository import OAuthStateRepository
from backend.services.oauth_ml_service import (
    build_ml_auth_url,
    build_ml_oauth_state,
    generate_pkce_pair,
    normalize_company_code,
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
) -> dict[str, str | None]:
    return {
        "provider": PROVIDER_ML,
        "message": "Callback recebido com sucesso.",
        "code": code,
        "state": state,
        "error": error,
    }
