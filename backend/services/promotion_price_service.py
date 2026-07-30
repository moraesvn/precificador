"""Cálculo puro de preço promocional (deal_price) a partir das configs."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any


MONEY_QUANT = Decimal("0.01")

DISCOUNT_RULE_KEYS = frozenset(
    {
        "premium_traditional_percent",
        "classic_traditional_percent",
        "premium_catalog_percent",
        "classic_catalog_percent",
        "other_percent",
    }
)


def to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def resolve_discount_rule_key(
    listing_type_id: str | None,
    catalog_listing: bool | None,
) -> str:
    """Mapeia exposição + catálogo para a chave de % nas configs."""
    listing_type = (listing_type_id or "").strip().lower()
    is_catalog = bool(catalog_listing)
    if listing_type == "gold_pro":
        return (
            "premium_catalog_percent" if is_catalog else "premium_traditional_percent"
        )
    if listing_type == "gold_special":
        return (
            "classic_catalog_percent" if is_catalog else "classic_traditional_percent"
        )
    return "other_percent"


def apply_global_adjust(
    base: Decimal,
    *,
    kind: str,
    value: Decimal,
) -> Decimal:
    kind_norm = (kind or "percent").strip().lower()
    if kind_norm == "fixed":
        return base + value
    # percent (default)
    return base * (Decimal("1") + (value / Decimal("100")))


def compute_deal_price(base_adjusted: Decimal, discount_percent: Decimal) -> Decimal:
    factor = Decimal("1") - (discount_percent / Decimal("100"))
    if factor < 0:
        factor = Decimal("0")
    return money(base_adjusted * factor)


def discount_percent_from_rules(
    rules: dict[str, Any] | None,
    rule_key: str,
) -> Decimal:
    raw = (rules or {}).get(rule_key)
    parsed = to_decimal(raw)
    if parsed is None:
        parsed = to_decimal((rules or {}).get("other_percent")) or Decimal("0")
    return parsed


def exposure_label(listing_type_id: str | None) -> str | None:
    mapping = {
        "gold_pro": "Premium",
        "gold_special": "Clássico",
        "free": "Grátis",
    }
    if not listing_type_id:
        return None
    return mapping.get(listing_type_id, listing_type_id)


def number_or_none(value: Any) -> float | None:
    parsed = to_decimal(value)
    return float(parsed) if parsed is not None else None
