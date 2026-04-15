from fastapi import APIRouter, HTTPException, Query

from backend.constants import PROVIDER_TINY
from backend.services.oauth_tiny_service import build_tiny_auth_url, build_tiny_oauth_state


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
) -> dict[str, str | None]:
    return {
        "provider": PROVIDER_TINY,
        "message": "Callback recebido com sucesso.",
        "code": code,
        "state": state,
        "error": error,
    }
