"""Apply de SELLER_CAMPAIGN: cria campanha e inclui itens com deal_price."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.models import MLListing
from backend.repositories.promotion_apply_repository import PromotionApplyRepository
from backend.repositories.promotion_settings_repository import PromotionSettingsRepository
from backend.services.ml_api_service import (
    MLApiError,
    criar_seller_campaign,
    incluir_item_seller_campaign,
)
from backend.services.promotion_price_service import money, to_decimal


MAX_CAMPAIGN_DAYS = 14


def _parse_local_date(value: str) -> date:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Data obrigatoria.")
    # Aceita YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS
    try:
        if "T" in raw:
            return datetime.fromisoformat(raw).date()
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise ValueError(
            f"Data invalida '{value}'. Use YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS."
        ) from exc


def _to_local_datetime_str(value: str, *, end_of_day: bool = False) -> str:
    d = _parse_local_date(value)
    if end_of_day:
        return f"{d.isoformat()}T00:00:00"
    return f"{d.isoformat()}T00:00:00"


def validate_campaign_dates(start_date: str, finish_date: str) -> tuple[str, str]:
    start = _parse_local_date(start_date)
    finish = _parse_local_date(finish_date)
    today = date.today()
    if start < today:
        raise ValueError("start_date nao pode ser anterior a hoje.")
    if finish < start:
        raise ValueError("finish_date nao pode ser anterior a start_date.")
    if (finish - start).days > MAX_CAMPAIGN_DAYS:
        raise ValueError(
            f"Periodo maximo da SELLER_CAMPAIGN e {MAX_CAMPAIGN_DAYS} dias."
        )
    return _to_local_datetime_str(start_date), _to_local_datetime_str(finish_date)


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Um deal_price por ITEM_ID (primeiro elegível vence; conflitos viram aviso)."""
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
            "is_active": raw.get("is_active"),
            "listing_type_id": raw.get("listing_type_id"),
            "warnings": list(raw.get("warnings") or []),
        }
        if item_id not in by_item:
            by_item[item_id] = entry
            order.append(item_id)
            continue
        existing = by_item[item_id]
        if (
            existing.get("deal_price") is not None
            and entry.get("deal_price") is not None
            and existing["deal_price"] != entry["deal_price"]
        ):
            existing["warnings"].append(
                f"ITEM_ID repetido com deal_price diferente "
                f"({existing['deal_price']} vs {entry['deal_price']}); "
                "mantido o primeiro."
            )
        if entry.get("sku") and not existing.get("sku"):
            existing["sku"] = entry["sku"]
    return [by_item[item_id] for item_id in order]


def _serialize_run(run: Any, items: list[Any] | None = None) -> dict[str, Any]:
    payload = {
        "id": run.id,
        "company_code": run.company_code,
        "marketplace": run.marketplace,
        "promotion_type": run.promotion_type,
        "ml_promotion_id": run.ml_promotion_id,
        "campaign_name": run.campaign_name,
        "start_date": run.start_date,
        "finish_date": run.finish_date,
        "status": run.status,
        "dry_run": run.dry_run,
        "items_total": run.items_total,
        "items_success": run.items_success,
        "items_failed": run.items_failed,
        "items_skipped": run.items_skipped,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }
    if items is not None:
        payload["items"] = [
            {
                "id": row.id,
                "item_id": row.item_id,
                "sku": row.sku,
                "deal_price": float(row.deal_price)
                if row.deal_price is not None
                else None,
                "status": row.status,
                "http_status": row.http_status,
                "response_body": row.response_body,
                "error_message": row.error_message,
            }
            for row in items
        ]
    return payload


def apply_seller_campaign(
    db: Session,
    *,
    company_code: str,
    marketplace: str,
    access_token: str,
    name: str | None,
    start_date: str | None,
    finish_date: str | None,
    promotion_id: str | None,
    items: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Cria (ou reutiliza) SELLER_CAMPAIGN e inclui itens com deal_price.

    Não reativa anúncios. Itens inativos / free / sem preço são skipped no log.
    """
    settings_repo = PromotionSettingsRepository(db)
    _, type_rows = settings_repo.ensure_defaults(
        company_code=company_code, marketplace=marketplace
    )
    type_row = next(
        (row for row in type_rows if row.promotion_type == "SELLER_CAMPAIGN"),
        None,
    )
    if type_row is None or not type_row.is_enabled:
        raise ValueError("SELLER_CAMPAIGN esta desativado nas configuracoes.")

    deduped = _dedupe_items(items)
    if not deduped:
        raise ValueError("Informe ao menos um item_id com deal_price.")

    enriched: list[dict[str, Any]] = []
    for entry in deduped:
        item_id = entry["item_id"]
        listing = (
            db.query(MLListing)
            .filter(
                MLListing.company_code == company_code.upper(),
                MLListing.item_id == item_id,
            )
            .first()
        )
        if listing is not None:
            entry["is_active"] = bool(listing.is_active and listing.status == "active")
            entry["listing_type_id"] = listing.listing_type_id
        enriched.append(entry)

    apply_repo = PromotionApplyRepository(db)
    campaign_name = (name or "").strip() or None
    ml_promotion_id = (promotion_id or "").strip() or None
    start_norm: str | None = None
    finish_norm: str | None = None

    if ml_promotion_id is None:
        if not campaign_name or not start_date or not finish_date:
            raise ValueError(
                "Para criar campanha informe name, start_date e finish_date "
                "(ou envie promotion_id existente)."
            )
        start_norm, finish_norm = validate_campaign_dates(start_date, finish_date)

    run = apply_repo.create_run(
        company_code=company_code,
        marketplace=marketplace,
        promotion_type="SELLER_CAMPAIGN",
        campaign_name=campaign_name,
        start_date=start_norm or (start_date.strip() if start_date else None),
        finish_date=finish_norm or (finish_date.strip() if finish_date else None),
        ml_promotion_id=ml_promotion_id,
        dry_run=dry_run,
        items_total=len(enriched),
        status="dry_run" if dry_run else "running",
    )

    success = 0
    failed = 0
    skipped = 0

    try:
        if ml_promotion_id is None:
            if dry_run:
                ml_promotion_id = "DRY_RUN_PROMOTION"
                apply_repo.update_run(run, ml_promotion_id=ml_promotion_id)
            else:
                created = criar_seller_campaign(
                    access_token,
                    name=campaign_name or f"Campanha {run.id}",
                    start_date=start_norm or "",
                    finish_date=finish_norm or "",
                )
                ml_promotion_id = str(created.get("id") or "").strip()
                if not ml_promotion_id:
                    raise ValueError("ML nao retornou id da campanha criada.")
                apply_repo.update_run(run, ml_promotion_id=ml_promotion_id)

        for entry in enriched:
            item_id = entry["item_id"]
            deal_price = entry.get("deal_price")
            warnings = list(entry.get("warnings") or [])

            if deal_price is None or Decimal(str(deal_price)) <= 0:
                skipped += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="skipped",
                    error_message="deal_price ausente ou <= 0",
                )
                continue

            if entry.get("is_active") is False:
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
                )
                continue

            listing_type = (entry.get("listing_type_id") or "").lower()
            if listing_type == "free":
                skipped += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="skipped",
                    error_message="Exposicao gratuita (free) nao elegivel.",
                )
                continue

            if dry_run:
                success += 1
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="success",
                    response_body={
                        "dry_run": True,
                        "would_post": {
                            "promotion_id": ml_promotion_id,
                            "promotion_type": "SELLER_CAMPAIGN",
                            "deal_price": deal_price,
                            "top_deal_price": entry.get("top_deal_price"),
                        },
                        "warnings": warnings,
                    },
                )
                continue

            try:
                response = incluir_item_seller_campaign(
                    access_token,
                    item_id,
                    promotion_id=ml_promotion_id,
                    deal_price=float(deal_price),
                    top_deal_price=entry.get("top_deal_price"),
                )
                success += 1
                body = dict(response) if isinstance(response, dict) else {"raw": response}
                if warnings:
                    body["warnings"] = warnings
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
                    status="success",
                    http_status=200,
                    response_body=body,
                )
            except MLApiError as exc:
                failed += 1
                response_body = (
                    exc.body if isinstance(exc.body, dict) else {"raw": exc.body}
                )
                apply_repo.add_item(
                    run_id=run.id,
                    item_id=item_id,
                    sku=entry.get("sku"),
                    deal_price=deal_price,
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
                    deal_price=deal_price,
                    status="failed",
                    error_message=str(exc)[:2000],
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

    item_rows = apply_repo.list_items(run.id)
    return _serialize_run(run, item_rows)


def get_apply_run(
    db: Session,
    *,
    company_code: str,
    run_id: int,
) -> dict[str, Any] | None:
    repo = PromotionApplyRepository(db)
    run = repo.get_run(run_id, company_code=company_code)
    if run is None:
        return None
    return _serialize_run(run, repo.list_items(run.id))
