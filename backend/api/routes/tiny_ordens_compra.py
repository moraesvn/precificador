from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.tiny_auth import get_tiny_access_token_with_optional_refresh
from backend.services.tiny_erp_api_service import listar_ordens_compra


router = APIRouter(prefix="/tiny/ordens-compra", tags=["tiny-ordens-compra"])


@router.get("")
@router.get("/")
def listar_ordens_compra_tiny(
    data_inicial: str = Query(
        ...,
        description="Data inicial do periodo (enviado para o Tiny como dataInicial).",
        example="2026-01-01",
    ),
    data_final: str = Query(
        ...,
        description="Data final do periodo (enviado para o Tiny como dataFinal).",
        example="2026-01-31",
    ),
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    limit: int = Query(default=100, ge=1, le=500, description="Quantidade maxima por pagina"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginacao"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Proxy seguro para listagem de ordens de compra no Tiny.

    O access token OAuth do Tiny permanece salvo no banco e o endpoint aceita
    apenas o token interno no header `X-Internal-Token`.
    """
    token = get_tiny_access_token_with_optional_refresh(db, company, x_internal_token)

    try:
        return listar_ordens_compra(
            token,
            data_inicial=data_inicial.strip(),
            data_final=data_final.strip(),
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
