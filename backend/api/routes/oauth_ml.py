from fastapi import APIRouter, HTTPException, Query

from backend.constants import PROVIDER_ML
from backend.services.oauth_ml_service import (
    build_ml_auth_url,
    build_ml_oauth_state,
    generate_pkce_pair,
)


router = APIRouter(prefix="/oauth/ml", tags=["oauth-ml"])


@router.get("/start")
def ml_start(company: str = Query(default="SP")) -> dict[str, str]:
    try:
        state = build_ml_oauth_state(company)
        code_verifier, code_challenge = generate_pkce_pair()
        auth_url = build_ml_auth_url(company, state, code_challenge)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "provider": PROVIDER_ML,
        "company_code": company.upper(),
        "state": state,
        "code_challenge_method": "S256",
        # Etapa 2: retornamos o verifier para teste local.
        # Na proxima etapa ele sera persistido server-side para usar no callback.
        "code_verifier": code_verifier,
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
