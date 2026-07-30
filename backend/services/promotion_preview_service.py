"""Orquestra prévia de promoção: Tiny + ofertas ML + configs → deal_price."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.models import MLListingRelation
from backend.repositories.ml_sync_repository import MLSyncRepository
from backend.repositories.promotion_settings_repository import PromotionSettingsRepository
from backend.services.promotion_price_service import (
    apply_global_adjust,
    compute_deal_price,
    discount_percent_from_rules,
    exposure_label,
    money,
    number_or_none,
    resolve_discount_rule_key,
    to_decimal,
)
from backend.services.promotion_types_catalog import (
    DEFAULT_DISCOUNT_RULES,
    get_catalog_entry,
)
from backend.services.tiny_erp_api_service import listar_produtos


def _serialize_relation(entry: MLListingRelation) -> dict[str, Any]:
    return {
        "id": entry.id,
        "company_code": entry.company_code,
        "seller_id": entry.seller_id,
        "source_item_id": entry.source_item_id,
        "related_item_id": entry.related_item_id,
        "related_variation_id": entry.related_variation_id or None,
        "stock_relation": entry.stock_relation,
    }


def _merge_discount_rules(raw: dict[str, Any] | None) -> dict[str, float]:
    merged = {key: float(value) for key, value in DEFAULT_DISCOUNT_RULES.items()}
    if not raw:
        return merged
    for key, value in raw.items():
        if key not in merged:
            continue
        try:
            merged[key] = float(value)
        except (TypeError, ValueError):
            continue
    return merged


def _extract_tiny_item(raw: dict[str, Any]) -> dict[str, Any]:
    precos = raw.get("precos") if isinstance(raw.get("precos"), dict) else {}
    price = to_decimal(precos.get("preco"))
    return {
        "id": raw.get("id"),
        "sku": str(raw.get("sku") or "").strip(),
        "name": raw.get("descricao") or raw.get("nome"),
        "price": float(price) if price is not None else None,
        "situacao": raw.get("situacao"),
    }


def fetch_tiny_by_sku(
    access_token: str,
    *,
    sku: str,
    data_alteracao: str,
    situacao: str | None = "A",
) -> dict[str, Any] | None:
    """Busca um produto Tiny pelo código/SKU (primeira página)."""
    try:
        payload = listar_produtos(
            access_token,
            data_alteracao=data_alteracao,
            limit=20,
            offset=0,
            codigo=sku.strip(),
            situacao=situacao,
        )
    except ValueError:
        return None

    itens = payload.get("itens") if isinstance(payload, dict) else None
    if not isinstance(itens, list):
        return None

    target = sku.strip().upper()
    for item in itens:
        if not isinstance(item, dict):
            continue
        parsed = _extract_tiny_item(item)
        if parsed["sku"].upper() == target:
            return parsed
    # Fallback: se Tiny retornou algo pelo filtro codigo, usa o primeiro.
    for item in itens:
        if isinstance(item, dict):
            return _extract_tiny_item(item)
    return None


def build_preview_for_skus(
    db: Session,
    *,
    company_code: str,
    marketplace: str,
    promotion_type: str,
    skus: list[str],
    items_override: list[dict[str, Any]] | None = None,
    tiny_access_token: str | None = None,
    tiny_data_alteracao: str = "2000-01-01 00:00:00",
    tiny_situacao: str | None = "A",
) -> dict[str, Any]:
    catalog = get_catalog_entry(promotion_type)
    if catalog is None:
        raise ValueError("Tipo de promocao desconhecido.")

    settings_repo = PromotionSettingsRepository(db)
    marketplace_row, type_rows = settings_repo.ensure_defaults(
        company_code=company_code,
        marketplace=marketplace,
    )
    type_row = next(
        (row for row in type_rows if row.promotion_type == catalog["code"]),
        None,
    )
    if type_row is None or not type_row.is_enabled:
        raise ValueError(
            f"Tipo {catalog['code']} esta desativado nas configuracoes."
        )

    discount_rules = _merge_discount_rules(type_row.discount_rules)
    price_base_source = (marketplace_row.price_base_source or "tiny").lower()
    adjust_kind = (marketplace_row.global_adjust_kind or "percent").lower()
    adjust_value = to_decimal(marketplace_row.global_adjust_value) or Decimal("0")

    override_by_sku: dict[str, dict[str, Any]] = {}
    if items_override:
        for item in items_override:
            sku_key = str(item.get("sku") or "").strip().upper()
            if sku_key:
                override_by_sku[sku_key] = item

    unique_skus: list[str] = []
    seen: set[str] = set()
    for sku in skus:
        key = str(sku or "").strip()
        if not key:
            continue
        upper = key.upper()
        if upper in seen:
            continue
        seen.add(upper)
        unique_skus.append(key)

    for sku_key in override_by_sku:
        if sku_key not in seen:
            seen.add(sku_key)
            unique_skus.append(sku_key)

    ml_repo = MLSyncRepository(db)
    preview_items: list[dict[str, Any]] = []

    for sku in unique_skus:
        sku_upper = sku.upper()
        warnings: list[str] = []
        tiny_info: dict[str, Any] | None = None

        override = override_by_sku.get(sku_upper)
        if override is not None:
            tiny_price = to_decimal(override.get("tiny_price"))
            tiny_info = {
                "id": override.get("tiny_id"),
                "sku": sku,
                "name": override.get("tiny_name"),
                "price": float(tiny_price) if tiny_price is not None else None,
                "situacao": override.get("situacao"),
            }
        elif tiny_access_token and price_base_source == "tiny":
            tiny_info = fetch_tiny_by_sku(
                tiny_access_token,
                sku=sku,
                data_alteracao=tiny_data_alteracao,
                situacao=tiny_situacao,
            )
            if tiny_info is None:
                warnings.append("Produto nao encontrado no Tiny.")
        elif price_base_source == "tiny":
            warnings.append(
                "Preco Tiny nao informado e busca Tiny nao disponivel nesta chamada."
            )

        pairs = ml_repo.find_offers_by_sku(
            company_code=company_code,
            sku=sku,
            active_only=False,
        )
        item_ids = [sku_row.item_id for sku_row, _ in pairs]
        relations = ml_repo.list_relations_for_items(
            company_code=company_code,
            item_ids=item_ids,
        )

        if not pairs:
            warnings.append("Nenhuma oferta ML encontrada no catalogo local.")

        offers_out: list[dict[str, Any]] = []
        seen_item_ids: set[str] = set()

        for sku_row, listing in pairs:
            offer_warnings: list[str] = []
            listing_type_id = listing.listing_type_id if listing else None
            catalog_listing = bool(listing.catalog_listing) if listing else False
            ml_price = to_decimal(listing.price) if listing else None
            is_active = bool(
                sku_row.is_active
                and (listing.is_active if listing is not None else False)
            )
            status = (listing.status if listing else sku_row.status) or None

            if not is_active:
                offer_warnings.append(
                    "Anuncio inativo — promocao exige MLB ativo; "
                    "o sistema nao reativa no POST."
                )
            if listing is None:
                offer_warnings.append("Listing nao vinculado no catalogo local.")

            if sku_row.item_id in seen_item_ids:
                offer_warnings.append(
                    "ITEM_ID repetido (variacao) — apply e por ITEM_ID."
                )
            seen_item_ids.add(sku_row.item_id)

            rule_key = resolve_discount_rule_key(listing_type_id, catalog_listing)
            discount_percent = discount_percent_from_rules(discount_rules, rule_key)

            tiny_price = to_decimal((tiny_info or {}).get("price"))
            if price_base_source == "ml":
                base = ml_price
                if base is None:
                    offer_warnings.append("Preco ML indisponivel para base.")
            else:
                base = tiny_price
                if base is None:
                    offer_warnings.append("Preco Tiny indisponivel para base.")

            base_adjusted: Decimal | None = None
            deal_price: Decimal | None = None
            if base is not None:
                base_adjusted = apply_global_adjust(
                    base, kind=adjust_kind, value=adjust_value
                )
                deal_price = compute_deal_price(base_adjusted, discount_percent)
                if deal_price <= 0:
                    offer_warnings.append("deal_price calculado <= 0.")

            offers_out.append(
                {
                    "item_id": sku_row.item_id,
                    "variation_id": sku_row.variation_id or None,
                    "seller_sku": sku_row.seller_sku,
                    "title": (listing.title if listing else sku_row.title),
                    "listing_type_id": listing_type_id,
                    "exposure": exposure_label(listing_type_id),
                    "catalog_listing": catalog_listing,
                    "ml_price": number_or_none(ml_price),
                    "status": status,
                    "is_active": is_active,
                    "permalink": listing.permalink if listing else None,
                    "discount_rule_key": rule_key,
                    "discount_percent": float(discount_percent),
                    "base_price": float(money(base)) if base is not None else None,
                    "base_price_adjusted": (
                        float(money(base_adjusted))
                        if base_adjusted is not None
                        else None
                    ),
                    "deal_price": (
                        float(deal_price) if deal_price is not None else None
                    ),
                    "eligible_for_apply": bool(
                        is_active and deal_price is not None and deal_price > 0
                    ),
                    "warnings": offer_warnings,
                }
            )

        preview_items.append(
            {
                "sku": sku,
                "tiny": tiny_info,
                "price_base_source": price_base_source,
                "offers_count": len(offers_out),
                "offers": offers_out,
                "relations": [_serialize_relation(rel) for rel in relations],
                "warnings": warnings,
            }
        )

    return {
        "company_code": company_code,
        "marketplace": marketplace,
        "promotion_type": catalog["code"],
        "promotion_name": catalog.get("name"),
        "mvp_supported": bool(catalog.get("mvp_supported")),
        "marketplace_settings": {
            "price_base_source": price_base_source,
            "global_adjust_kind": adjust_kind,
            "global_adjust_value": float(adjust_value),
        },
        "discount_rules_used": discount_rules,
        "items_count": len(preview_items),
        "items": preview_items,
        "note": (
            "Previa apenas — nenhum POST de promocao foi enviado ao Mercado Livre."
        ),
    }
