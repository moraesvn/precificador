from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.ml_auth import get_ml_access_token_with_optional_refresh
from backend.services.ml_api_service import obter_preco_venda, obter_precos_item


router = APIRouter(prefix="/ml/items", tags=["ml-precos"])


@router.get("/{item_id}/prices")
def listar_precos_ml(
    item_id: str,
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Proxy seguro para GET /items/{item_id}/prices da API do Mercado Livre.

    Retorna todos os preços válidos do anúncio (standard e promotion).
    """
    token = get_ml_access_token_with_optional_refresh(db, company, x_internal_token)

    try:
        return obter_precos_item(token, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{item_id}/sale_price")
def obter_preco_venda_ml(
    item_id: str,
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    context: str | None = Query(
        default=None,
        description=(
            "Canal e/ou nível de fidelidade, separados por vírgula. "
            "Ex.: channel_marketplace,buyer_loyalty_3"
        ),
        example="channel_marketplace",
    ),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Proxy seguro para GET /items/{item_id}/sale_price da API do Mercado Livre.

    Retorna o preço de venda vencedor para o contexto informado.
    """
    token = get_ml_access_token_with_optional_refresh(db, company, x_internal_token)

    try:
        return obter_preco_venda(token, item_id, context=context)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
