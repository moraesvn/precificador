from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.ml_auth import get_ml_connection_with_optional_refresh
from backend.services.ml_api_service import buscar_itens_vendedor, obter_usuario_autenticado


router = APIRouter(prefix="/ml", tags=["ml-conta"])


@router.get("/me")
def obter_perfil_ml(
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Proxy seguro para GET /users/me da API do Mercado Livre.

    Valida o token OAuth salvo sem precisar informar item_id.
    """
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)

    try:
        return obter_usuario_autenticado(connection.access_token)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/items/search")
def buscar_anuncios_ml(
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    status: str | None = Query(
        default="active",
        description="Filtro de status do anúncio (ex.: active, paused, closed).",
    ),
    limit: int = Query(default=10, ge=1, le=50, description="Quantidade por página"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginação"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Proxy seguro para GET /users/{user_id}/items/search.

    Usa o user_id salvo na conexão OAuth; se ausente, consulta /users/me antes.
    """
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    user_id = (connection.external_account_id or "").strip()

    try:
        if not user_id:
            profile = obter_usuario_autenticado(connection.access_token)
            user_id = str(profile.get("id", "")).strip()
        if not user_id:
            raise ValueError("Nao foi possivel obter user_id do Mercado Livre.")

        return buscar_itens_vendedor(
            connection.access_token,
            user_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
