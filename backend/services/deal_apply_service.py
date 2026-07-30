"""Consulta candidatos e apply de campanhas DEAL (tradicionais)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.models import MLListing
from backend.repositories.promotion_apply_repository import PromotionApplyRepository
from backend.repositories.promotion_settings_repository import PromotionSettingsRepository
from backend.services.ml_api_service import (
    MLApiError,
    incluir_item_promocao,
    listar_itens_promocao,
    listar_promocoes_vendedor,
)
from backend.services.promotion_price_service import money, number_or_none, to_decimal
from backend.services.seller_campaign_apply_service import _serialize_run


def list_deal_promotions(access_token: str, user_id: str) -> dict[str, Any]:
    """Lista promoções DEAL do vendedor (filtra type no client se preciso)."""
    payload = listar_promocoes_vendedor(
        access_token, user_id, promotion_type="DEAL"
    )
    results = payload.get("results")
    if not isinstance(results, list):
        results = []

    deals: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        promo_type = str(
            item.get("type") or item.get("promotion_type") or ""
        ).upper()
        if promo_type and promo_type != "DEAL":
            continue
        deals.append(
            {
                "id": item.get("id"),
                "type": promo_type or "DEAL",
                "status": item.get("status"),
                "name": item.get("name"),
                "start_date": item.get("start_date"),
                "finish_date": item.get("finish_date") or item.get("end_date"),
                "deadline_date": item.get("deadline_date"),
            }
        )

    return {
        "user_id": str(user_id),
        "promotion_type": "DEAL",
        "results": deals,
        "count": len(deals),
        "raw_paging": payload.get("paging"),
    }


def _normalize_candidate_row(raw: dict[str, Any]) -> dict[str, Any]:
    item_id = str(raw.get("id") or raw.get("item_id") or "").strip().upper()
    status = str(raw.get("status") or "").strip().lower() or None
    min_price = to_decimal(raw.get("min_discounted_price"))
    max_price = to_decimal(raw.get("max_discounted_price"))
    suggested = to_decimal(raw.get("suggested_discounted_price"))
    return {
        "item_id": item_id,
        "status": status,
        "is_candidate": status == "candidate",
        "price": number_or_none(raw.get("price")),
        "original_price": number_or_none(raw.get("original_price")),
        "min_discounted_price": float(min_price) if min_price is not None else None,
        "max_discounted_price": float(max_price) if max_price is not None else None,
        "suggested_discounted_price": (
            float(suggested) if suggested is not None else None
        ),
        "start_date": raw.get("start_date"),
        "end_date": raw.get("end_date") or raw.get("finish_date"),
        "offer_id": raw.get("offer_id"),
    }


def fetch_deal_candidates(
    access_token: str,
    *,
    promotion_id: str,
    item_ids: list[str],
) -> dict[str, Any]:
    """Consulta status/faixa de preço DEAL para uma lista de ITEM_IDs."""
    promotion_id = promotion_id.strip()
    if not promotion_id:
        raise ValueError("promotion_id obrigatorio.")

    unique_ids: list[str] = []
    seen: set[str] = set()
    for item_id in item_ids:
        key = str(item_id or "").strip().upper()
        if not key or key in seen:
            continue
        seen.add(key)
        unique_ids.append(key)

    results: list[dict[str, Any]] = []
    for item_id in unique_ids:
        try:
            payload = listar_itens_promocao(
                access_token,
                promotion_id,
                promotion_type="DEAL",
                item_id=item_id,
                limit=50,
                offset=0,
            )
        except MLApiError as exc:
            results.append(
                {
                    "item_id": item_id,
                    "status": None,
                    "is_candidate": False,
                    "error": str(exc)[:500],
                    "http_status": exc.status_code,
                }
            )
            continue

        rows = payload.get("results")
        if not isinstance(rows, list) or not rows:
            results.append(
                {
                    "item_id": item_id,
                    "status": None,
                    "is_candidate": False,
                    "found": False,
                    "warning": "Item nao encontrado nesta promocao DEAL.",
                }
            )
            continue

        # Preferência: linha do próprio item_id
        chosen = None
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized = _normalize_candidate_row(row)
            if normalized["item_id"] == item_id:
                chosen = normalized
                break
        if chosen is None and isinstance(rows[0], dict):
            chosen = _normalize_candidate_row(rows[0])
            chosen["item_id"] = item_id
        if chosen is None:
            results.append(
                {
                    "item_id": item_id,
                    "status": None,
                    "is_candidate": False,
                    "found": False,
                }
            )
            continue
        chosen["found"] = True
        results.append(chosen)

    return {
        "promotion_id": promotion_id,
        "promotion_type": "DEAL",
        "results": results,
        "count": len(results),
        "candidates_count": sum(1 for row in results if row.get("is_candidate")),
    }


def _price_in_band(
    deal_price: Decimal,
    min_price: Decimal | None,
    max_price: Decimal | None,
) -> tuple[bool, str | None]:
    if min_price is not None and deal_price < min_price:
        return False, (
            f"deal_price {float(deal_price)} abaixo do minimo "
            f"{float(min_price)} (ERROR_CREDIBILITY_DISCOUNTED_PRICE)."
        )
    if max_price is not None and deal_price > max_price:
        return False, (
            f"deal_price {float(deal_price)} acima do maximo "
            f"{float(max_price)} (ERROR_CREDIBILITY_DISCOUNTED_PRICE)."
        )
    return True, None


def _clamp_price(
    deal_price: Decimal,
    min_price: Decimal | None,
    max_price: Decimal | None,
) -> Decimal:
    value = deal_price
    if min_price is not None and value < min_price:
        value = min_price
    if max_price is not None and value > max_price:
        value = max_price
    return money(value)


def apply_deal(
    db: Session,
    *,
    company_code: str,
    marketplace: str,
    access_token: str,
    promotion_id: str,
    items: list[dict[str, Any]],
    dry_run: bool = False,
    clamp_to_band: bool = False,
) -> dict[str, Any]:
    """
    Aderir itens candidatos a uma DEAL com deal_price.

    Reusa promotion_apply_runs / promotion_apply_items.
    Não reativa anúncios. Fora da faixa → skip (ou clamp se pedido).
    """
    settings_repo = PromotionSettingsRepository(db)
    _, type_rows = settings_repo.ensure_defaults(
        company_code=company_code, marketplace=marketplace
    )
    type_row = next(
        (row for row in type_rows if row.promotion_type == "DEAL"),
        None,
    )
    if type_row is None or not type_row.is_enabled:
        raise ValueError("DEAL esta desativado nas configuracoes.")

    promotion_id = promotion_id.strip()
    if not promotion_id:
        raise ValueError("promotion_id obrigatorio para DEAL.")

    # Dedup por ITEM_ID
    by_item: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for raw in items:
        item_id = str(raw.get("item_id") or "").strip().upper()
        if not item_id:
            continue
        deal = to_decimal(raw.get("deal_price"))
        entry = {
            "item_id": item_id,
            "sku": (str(raw.get("sku")).strip() if raw.get("sku") else None),
            "deal_price": float(money(deal)) if deal is not None else None,
            "top_deal_price": (
                float(money(to_decimal(raw.get("top_deal_price"))))
                if raw.get("top_deal_price") is not None
                and to_decimal(raw.get("top_deal_price")) is not None
                else None
            ),
        }
        if item_id not in by_item:
            by_item[item_id] = entry
            order.append(item_id)

    if not order:
        raise ValueError("Informe ao menos um item_id com deal_price.")

    candidates_payload = fetch_deal_candidates(
        access_token,
        promotion_id=promotion_id,
        item_ids=order,
    )
    candidate_by_id = {
        str(row.get("item_id") or "").upper(): row
        for row in candidates_payload.get("results") or []
        if isinstance(row, dict)
    }

    apply_repo = PromotionApplyRepository(db)
    run = apply_repo.create_run(
        company_code=company_code,
        marketplace=marketplace,
        promotion_type="DEAL",
        campaign_name=None,
        start_date=None,
        finish_date=None,
        ml_promotion_id=promotion_id,
        dry_run=dry_run,
        items_total=len(order),
        status="dry_run" if dry_run else "running",
    )

    success = 0
    failed = 0
    skipped = 0

    try:
        for item_id in order:
            entry = by_item[item_id]
            deal_price = entry.get("deal_price")
            candidate = candidate_by_id.get(item_id) or {}

            listing = (
                db.query(MLListing)
                .filter(
                    MLListing.company_code == company_code.upper(),
                    MLListing.item_id == item_id,
                )
                .first()
            )
            is_active = True
            if listing is not None:
                is_active = bool(listing.is_active and listing.status == "active")

            if deal_price is None or Decimal(str(deal_price)) <= 0:
                skipped += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="skipped",
                    error_message="deal_price ausente ou <= 0",
                    response_body={"candidate": candidate},
                )
                continue

            if not is_active:
                skipped += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="skipped",
                    error_message=(
                        "Anuncio inativo — promocao exige MLB ativo; "
                        "sistema nao reativa."
                    ),
                    response_body={"candidate": candidate},
                )
                continue

            if not candidate.get("is_candidate"):
                skipped += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="skipped",
                    error_message=(
                        f"Item nao e candidate nesta DEAL "
                        f"(status={candidate.get('status')})."
                    ),
                    response_body={"candidate": candidate},
                )
                continue

            deal_dec = Decimal(str(deal_price))
            min_p = to_decimal(candidate.get("min_discounted_price"))
            max_p = to_decimal(candidate.get("max_discounted_price"))
            in_band, band_error = _price_in_band(deal_dec, min_p, max_p)
            final_price = deal_dec
            clamped = False
            if not in_band:
                if clamp_to_band and (min_p is not None or max_p is not None):
                    final_price = _clamp_price(deal_dec, min_p, max_p)
                    clamped = True
                else:
                    skipped += 1
                    apply_repo.add_item(
                        run_id=run.id,
                        item_id=item_id,
                        sku=entry.get("sku"),
                        deal_price=deal_price,
                        status="skipped",
                        error_message=band_error,
                        response_body={"candidate": candidate},
                    )
                    continue

            final_float = float(money(final_price))

            if dry_run:
                success += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=final_float,
                    status="success",
                    response_body={
                        "dry_run": True,
                        "clamped": clamped,
                        "requested_deal_price": deal_price,
                        "would_post": {
                            "promotion_id": promotion_id,
                            "promotion_type": "DEAL",
                            "deal_price": final_float,
                            "top_deal_price": entry.get("top_deal_price"),
                        },
                        "candidate": candidate,
                    },
                )
                continue

            try:
                response = incluir_item_promocao(
                    access_token,
                    item_id,
                    promotion_id=promotion_id,
                    promotion_type="DEAL",
                    deal_price=final_float,
                    top_deal_price=entry.get("top_deal_price"),
                )
                success += 1
                body = dict(response) if isinstance(response, dict) else {"raw": response}
                body["candidate"] = candidate
                body["clamped"] = clamped
                body["requested_deal_price"] = deal_price
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=final_float,
                    status="success",
                    http_status=200,
                    response_body=body,
                )
            except MLApiError as exc:
                failed += 1
                response_body = (
                    exc.body if isinstance(exc.body, dict) else {"raw": exc.body}
                )
                if isinstance(response_body, dict):
                    response_body = {**response_body, "candidate": candidate}
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=final_float,
                    status="failed",
                    http_status=exc.status_code,
                    response_body=response_body,
                    error_message=str(exc)[:2000],
                )
            except ValueError as exc:
                failed += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=final_float,
                    status="failed",
                    error_message=str(exc)[:2000],
                    response_body={"candidate": candidate},
                )

        final_status = "dry_run" if dry_run else "completed"
        run = apply_repo.update_run(
            run,
            status=final_status,
            items_success=success,
            items_failed=failed,
            items_skipped=skipped,
            finished=True,
        )
    except Exception as exc:
        run = apply_repo.update_run(
            run,
            status="failed",
            items_success=success,
            items_failed=failed,
            items_skipped=skipped,
            error_message=str(exc)[:2000],
            finished=True,
        )
        raise

    return _serialize_run(run, apply_repo.list_items(run.id))
