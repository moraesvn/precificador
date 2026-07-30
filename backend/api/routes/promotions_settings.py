from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.tiny_auth import ensure_internal_token
from backend.repositories.promotion_settings_repository import PromotionSettingsRepository
from backend.services.oauth_ml_service import normalize_company_code
from backend.services.promotion_types_catalog import (
    DEFAULT_DISCOUNT_RULES,
    get_catalog_entry,
    get_promotion_type_catalog,
)


router = APIRouter(prefix="/promotions", tags=["promotions-settings"])

ALLOWED_MARKETPLACES = frozenset({"ml"})
ALLOWED_PRICE_SOURCES = frozenset({"tiny", "ml"})
ALLOWED_ADJUST_KINDS = frozenset({"percent", "fixed"})
DISCOUNT_RULE_KEYS = frozenset(DEFAULT_DISCOUNT_RULES.keys())


class MarketplaceSettingsUpdate(BaseModel):
    price_base_source: str | None = Field(
        default=None, description="tiny | ml — fonte do preço-base para cálculo"
    )
    global_adjust_kind: str | None = Field(
        default=None, description="percent | fixed — tipo do ajuste global"
    )
    global_adjust_value: float | None = Field(
        default=None, description="Valor do ajuste (ex.: 5 para +5% ou +R$ 5)"
    )


class PromotionTypeSettingsUpdate(BaseModel):
    is_enabled: bool | None = None
    discount_rules: dict[str, float] | None = None


def _normalize_marketplace(marketplace: str) -> str:
    value = (marketplace or "").strip().lower()
    if value not in ALLOWED_MARKETPLACES:
        raise HTTPException(
            status_code=400,
            detail=f"Marketplace invalido. Use: {', '.join(sorted(ALLOWED_MARKETPLACES))}",
        )
    return value


def _number(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _serialize_marketplace(row: Any) -> dict[str, Any]:
    return {
        "company_code": row.company_code,
        "marketplace": row.marketplace,
        "price_base_source": row.price_base_source,
        "global_adjust_kind": row.global_adjust_kind,
        "global_adjust_value": _number(row.global_adjust_value),
    }


def _merge_discount_rules(raw: dict[str, Any] | None) -> dict[str, float]:
    merged = {key: float(value) for key, value in DEFAULT_DISCOUNT_RULES.items()}
    if not raw:
        return merged
    for key, value in raw.items():
        if key not in DISCOUNT_RULE_KEYS:
            continue
        try:
            merged[key] = float(value)
        except (TypeError, ValueError):
            continue
    return merged


def _serialize_type_row(row: Any, catalog: dict[str, Any] | None) -> dict[str, Any]:
    payload = {
        "promotion_type": row.promotion_type,
        "is_enabled": row.is_enabled,
        "discount_rules": _merge_discount_rules(row.discount_rules),
        "mvp_supported": bool(catalog.get("mvp_supported")) if catalog else False,
        "name": catalog.get("name") if catalog else row.promotion_type,
        "summary": catalog.get("summary") if catalog else "",
        "created_by": catalog.get("created_by") if catalog else None,
        "price_mode": catalog.get("price_mode") if catalog else None,
        "meli_bonus": catalog.get("meli_bonus") if catalog else None,
    }
    return payload


@router.get("/types")
def list_promotion_types_catalog(
    x_internal_token: str | None = Header(default=None),
) -> dict:
    """Lista o catálogo resumido de tipos (sem estado por empresa)."""
    ensure_internal_token(x_internal_token)
    return {"results": get_promotion_type_catalog()}


@router.get("/settings")
def get_promotion_settings(
    company: str = Query(default="SP"),
    marketplace: str = Query(default="ml"),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Retorna regras gerais + tipos com ativação e % por eixo."""
    ensure_internal_token(x_internal_token)
    try:
        company_code = normalize_company_code(company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    market = _normalize_marketplace(marketplace)
    repo = PromotionSettingsRepository(db)
    marketplace_row, type_rows = repo.ensure_defaults(
        company_code=company_code, marketplace=market
    )
    catalog_by_code = {item["code"]: item for item in get_promotion_type_catalog()}
    return {
        "marketplace_settings": _serialize_marketplace(marketplace_row),
        "promotion_types": [
            _serialize_type_row(row, catalog_by_code.get(row.promotion_type))
            for row in type_rows
        ],
    }


@router.put("/settings/marketplace")
def update_marketplace_promotion_settings(
    body: MarketplaceSettingsUpdate,
    company: str = Query(default="SP"),
    marketplace: str = Query(default="ml"),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Atualiza fonte do preço-base e ajuste global."""
    ensure_internal_token(x_internal_token)
    try:
        company_code = normalize_company_code(company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    market = _normalize_marketplace(marketplace)
    if body.price_base_source is not None:
        source = body.price_base_source.strip().lower()
        if source not in ALLOWED_PRICE_SOURCES:
            raise HTTPException(
                status_code=400,
                detail="price_base_source deve ser 'tiny' ou 'ml'.",
            )
        body.price_base_source = source
    if body.global_adjust_kind is not None:
        kind = body.global_adjust_kind.strip().lower()
        if kind not in ALLOWED_ADJUST_KINDS:
            raise HTTPException(
                status_code=400,
                detail="global_adjust_kind deve ser 'percent' ou 'fixed'.",
            )
        body.global_adjust_kind = kind
    if body.global_adjust_value is not None:
        try:
            Decimal(str(body.global_adjust_value))
        except (InvalidOperation, ValueError) as exc:
            raise HTTPException(
                status_code=400, detail="global_adjust_value invalido."
            ) from exc

    repo = PromotionSettingsRepository(db)
    row = repo.update_marketplace_settings(
        company_code=company_code,
        marketplace=market,
        price_base_source=body.price_base_source,
        global_adjust_kind=body.global_adjust_kind,
        global_adjust_value=body.global_adjust_value,
    )
    return {"marketplace_settings": _serialize_marketplace(row)}


@router.put("/settings/types/{promotion_type}")
def update_promotion_type_settings(
    promotion_type: str,
    body: PromotionTypeSettingsUpdate,
    company: str = Query(default="SP"),
    marketplace: str = Query(default="ml"),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Ativa/desativa um tipo e atualiza % por exposição/catálogo."""
    ensure_internal_token(x_internal_token)
    try:
        company_code = normalize_company_code(company)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    market = _normalize_marketplace(marketplace)
    catalog = get_catalog_entry(promotion_type)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Tipo de promocao desconhecido.")

    discount_rules = None
    if body.discount_rules is not None:
        unknown = set(body.discount_rules) - DISCOUNT_RULE_KEYS
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Chaves invalidas em discount_rules: {sorted(unknown)}",
            )
        discount_rules = _merge_discount_rules(body.discount_rules)

    repo = PromotionSettingsRepository(db)
    row = repo.upsert_type_setting(
        company_code=company_code,
        marketplace=market,
        promotion_type=catalog["code"],
        is_enabled=body.is_enabled,
        discount_rules=discount_rules,
    )
    return {
        "promotion_type": _serialize_type_row(row, catalog),
    }
