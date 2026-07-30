"""Prévia de promoção (sem POST ao Mercado Livre)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.tiny_auth import (
    ensure_internal_token,
    get_tiny_access_token_with_optional_refresh,
)
from backend.services.oauth_ml_service import normalize_company_code
from backend.services.promotion_preview_service import build_preview_for_skus
from backend.services.promotion_types_catalog import get_catalog_entry


router = APIRouter(prefix="/promotions", tags=["promotions-preview"])

ALLOWED_MARKETPLACES = frozenset({"ml"})


class PreviewItemInput(BaseModel):
    sku: str = Field(..., description="SKU Tiny / SELLER_SKU")
    tiny_id: int | None = None
    tiny_name: str | None = None
    tiny_price: float | None = None
    situacao: str | None = None


class PreviewRequest(BaseModel):
    company: str = Field(default="SP")
    marketplace: str = Field(default="ml")
    promotion_type: str = Field(
        ...,
        description="Ex.: SELLER_CAMPAIGN ou DEAL",
    )
    skus: list[str] = Field(
        default_factory=list,
        description="SKUs a pré-visualizar (opcional se items for enviado)",
    )
    items: list[PreviewItemInput] = Field(
        default_factory=list,
        description="Itens com preço Tiny já resolvido (evita nova busca)",
    )
    tiny_data_alteracao: str = Field(
        default="2000-01-01 00:00:00",
        description="Usado na busca Tiny quando o preço não vem em items",
    )
    tiny_situacao: str | None = Field(
        default="A",
        description="Filtro situacao Tiny na busca por SKU",
    )
    fetch_tiny: bool = Field(
        default=True,
        description="Se true e faltar preço Tiny, busca na API Tiny",
    )


@router.post("/preview")
def preview_promotion(
    body: PreviewRequest,
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Calcula deal_price por oferta ML — não envia promoção ao ML."""
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

    catalog = get_catalog_entry(body.promotion_type)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Tipo de promocao desconhecido.")

    skus = [str(sku).strip() for sku in body.skus if str(sku).strip()]
    items_override = [
        {
            "sku": item.sku,
            "tiny_id": item.tiny_id,
            "tiny_name": item.tiny_name,
            "tiny_price": item.tiny_price,
            "situacao": item.situacao,
        }
        for item in body.items
        if str(item.sku or "").strip()
    ]
    if not skus and not items_override:
        raise HTTPException(
            status_code=400,
            detail="Informe ao menos um SKU em skus ou items.",
        )

    tiny_token: str | None = None
    if body.fetch_tiny:
        try:
            tiny_token = get_tiny_access_token_with_optional_refresh(
                db, company_code, x_internal_token
            )
        except HTTPException:
            # Mantém prévia com ofertas ML; avisos indicam falta do Tiny.
            tiny_token = None

    try:
        return build_preview_for_skus(
            db,
            company_code=company_code,
            marketplace=marketplace,
            promotion_type=catalog["code"],
            skus=skus,
            items_override=items_override or None,
            tiny_access_token=tiny_token,
            tiny_data_alteracao=body.tiny_data_alteracao.strip(),
            tiny_situacao=(body.tiny_situacao or "").strip().upper() or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
