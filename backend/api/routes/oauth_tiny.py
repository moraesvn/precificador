from fastapi import APIRouter, Query


router = APIRouter(prefix="/oauth/tiny", tags=["oauth-tiny"])


@router.get("/callback")
def tiny_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> dict[str, str | None]:
    return {
        "provider": "tiny",
        "message": "Callback recebido com sucesso.",
        "code": code,
        "state": state,
        "error": error,
    }
