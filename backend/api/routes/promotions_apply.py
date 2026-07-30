"""Apply de promoções no Mercado Livre + consulta de log."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.ml_auth import get_ml_connection_with_optional_refresh
from backend.api.routes.tiny_auth import ensure_internal_token
from backend.services.deal_apply_service import (
    apply_deal,
    fetch_deal_candidates,
    list_deal_promotions,
)
from backend.services.ml_api_service import MLApiError
from backend.services.oauth_ml_service import normalize_company_code
from backend.services.seller_campaign_apply_service import (
    apply_seller_campaign,
    get_apply_run,
)


router = APIRouter(prefix="/promotions", tags=["promotions-apply"])

ALLOWED_MARKETPLACES = frozenset({"ml"})


class ApplyItemInput(BaseModel):
    item_id: str
    deal_price: float
    sku: str | None = None
    top_deal_price: float | None = None
    is_active: bool | None = None
    listing_type_id: str | None = None


class SellerCampaignApplyRequest(BaseModel):
    company: str = Field(default="SP")
    marketplace: str = Field(default="ml")
    name: str | None = Field(
        default=None,
        description="Nome da campanha (obrigatório se não houver promotion_id)",
    )
    start_date: str | None = Field(
        default=None,
        description="Início local YYYY-MM-DD (obrigatório se criar campanha)",
    )
    finish_date: str | None = Field(
        default=None,
        description="Fim local YYYY-MM-DD (máx. 14 dias; obrigatório se criar)",
    )
    promotion_id: str | None = Field(
        default=None,
        description="ID existente (ex.: C-MLB123). Se omitido, cria nova campanha.",
    )
    items: list[ApplyItemInput] = Field(default_factory=list)
    dry_run: bool = Field(
        default=False,
        description="Se true, valida e registra log sem POST no ML",
    )


class DealCandidatesRequest(BaseModel):
    company: str = Field(default="SP")
    promotion_id: str
    item_ids: list[str] = Field(default_factory=list)


class DealApplyRequest(BaseModel):
    company: str = Field(default="SP")
    marketplace: str = Field(default="ml")
    promotion_id: str = Field(..., description="ID da DEAL (ex.: P-MLB...)")
    items: list[ApplyItemInput] = Field(default_factory=list)
    dry_run: bool = False
    clamp_to_band: bool = Field(
        default=False,
        description="Se true, ajusta deal_price para min/max da faixa crível",
    )


@router.post("/apply/seller-campaign")
def apply_seller_campaign_route(
    body: SellerCampaignApplyRequest,
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Cria/reutiliza SELLER_CAMPAIGN e inclui itens com deal_price + log."""
    ensure_internal_token(x_internal_token)

    try:
        company_code = normalize_company_code(body.company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    marketplace = (body.marketplace or "").strip().lower()
    if marketplace not in ALLOWED_MARKETPLACES:
        raise HTTPException(
            status_code=400,
            detail=f"Marketplace invalido. Use: {', '.join(sorted(ALLOWED_MARKETPLACES))}",
        )

    if not body.items:
        raise HTTPException(status_code=400, detail="Informe ao menos um item.")

    connection = get_ml_connection_with_optional_refresh(
        db, company_code, x_internal_token
    )

    items_payload = [item.model_dump() for item in body.items]
    try:
        return apply_seller_campaign(
            db,
            company_code=company_code,
            marketplace=marketplace,
            access_token=connection.access_token,
            name=body.name,
            start_date=body.start_date,
            finish_date=body.finish_date,
            promotion_id=body.promotion_id,
            items=items_payload,
            dry_run=bool(body.dry_run),
        )
    except MLApiError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/deals")
def list_deals_route(
    company: str = Query(default="SP"),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Lista campanhas DEAL (tradicionais) do vendedor autenticado."""
    connection = get_ml_connection_with_optional_refresh(
        db, company, x_internal_token
    )
    user_id = (connection.external_account_id or "").strip()
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Conexao ML sem user_id. Execute refresh OAuth do ML.",
        )
    try:
        return list_deal_promotions(connection.access_token, user_id)
    except MLApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/deals/candidates")
def deal_candidates_route(
    body: DealCandidatesRequest,
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Consulta se ITEM_IDs são candidatos na DEAL e a faixa de preço."""
    connection = get_ml_connection_with_optional_refresh(
        db, body.company, x_internal_token
    )
    if not body.item_ids:
        raise HTTPException(status_code=400, detail="Informe ao menos um item_id.")
    try:
        return fetch_deal_candidates(
            connection.access_token,
            promotion_id=body.promotion_id,
            item_ids=body.item_ids,
        )
    except MLApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/apply/deal")
def apply_deal_route(
    body: DealApplyRequest,
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Aderir candidatos a uma DEAL com deal_price + log."""
    ensure_internal_token(x_internal_token)

    try:
        company_code = normalize_company_code(body.company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    marketplace = (body.marketplace or "").strip().lower()
    if marketplace not in ALLOWED_MARKETPLACES:
        raise HTTPException(
            status_code=400,
            detail=f"Marketplace invalido. Use: {', '.join(sorted(ALLOWED_MARKETPLACES))}",
        )
    if not body.items:
        raise HTTPException(status_code=400, detail="Informe ao menos um item.")

    connection = get_ml_connection_with_optional_refresh(
        db, company_code, x_internal_token
    )
    try:
        return apply_deal(
            db,
            company_code=company_code,
            marketplace=marketplace,
            access_token=connection.access_token,
            promotion_id=body.promotion_id,
            items=[item.model_dump() for item in body.items],
            dry_run=bool(body.dry_run),
            clamp_to_band=bool(body.clamp_to_band),
        )
    except MLApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/apply/{run_id}")
def get_promotion_apply_run(
    run_id: int,
    company: str = Query(default="SP"),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Consulta log de um apply (run + itens)."""
    ensure_internal_token(x_internal_token)
    try:
        company_code = normalize_company_code(company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = get_apply_run(db, company_code=company_code, run_id=run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Apply run nao encontrado.")
    return payload
