from fastapi import APIRouter, Query


router = APIRouter(prefix="/oauth/ml", tags=["oauth-ml"])


@router.get("/callback")
@router.get("/callback/")
def ml_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> dict[str, str | None]:
    return {
        "provider": "ml",
        "message": "Callback recebido com sucesso.",
        "code": code,
        "state": state,
        "error": error,
    }
