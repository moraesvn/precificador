from __future__ import annotations

import json
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from backend.db import SessionLocal
from backend.repositories.ml_sync_repository import MLSyncRepository
from backend.services.ml_api_service import (
    buscar_itens_catalog_boost_ativos,
    buscar_todos_itens_ativos_vendedor,
    obter_itens_em_lote,
)

DETAIL_BATCH_SIZE = 20


def normalize_seller_sku(value: str | None) -> str | None:
    """Normaliza o SKU para busca sem alterar o valor original armazenado."""
    normalized = (value or "").strip().upper()
    return normalized or None


def _get_seller_sku(attributes: Any) -> str | None:
    if not isinstance(attributes, list):
        return None

    for attribute in attributes:
        if not isinstance(attribute, dict) or attribute.get("id") != "SELLER_SKU":
            continue
        value = str(attribute.get("value_name") or "").strip()
        return value or None
    return None


def _parse_ml_datetime(value: Any) -> datetime | None:
    raw_value = str(value or "").strip()
    if not raw_value:
        return None
    try:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _json_list(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    return json.dumps(value, ensure_ascii=False)


def extract_sku_records(
    item: dict[str, Any],
    *,
    company_code: str,
    seller_id: str,
    listing_id: int | None,
    run_id: int,
    synced_at: datetime,
) -> list[dict[str, Any]]:
    """Converte o detalhe de um anúncio em registros SKU por item/variação."""
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        raise ValueError("Detalhe de anuncio sem item_id.")

    title = str(item.get("title") or "").strip() or None
    status = str(item.get("status") or "").strip().lower() or "unknown"
    is_active = status == "active"
    ml_last_updated = _parse_ml_datetime(item.get("last_updated"))
    item_sku = _get_seller_sku(item.get("attributes"))
    common_values = {
        "listing_id": listing_id,
        "company_code": company_code.upper(),
        "seller_id": seller_id,
        "item_id": item_id,
        "title": title,
        "status": status,
        "is_active": is_active,
        "ml_last_updated": ml_last_updated,
        "last_seen_at": synced_at,
        "last_synced_at": synced_at,
        "last_sync_run_id": run_id,
    }
    records: list[dict[str, Any]] = []
    variations = item.get("variations")

    if isinstance(variations, list) and variations:
        for variation in variations:
            if not isinstance(variation, dict):
                continue
            variation_id = str(variation.get("id") or "").strip()
            if not variation_id:
                continue
            variation_sku = _get_seller_sku(variation.get("attributes"))
            records.append(
                {
                    **common_values,
                    "variation_id": variation_id,
                    "seller_sku": variation_sku,
                    "normalized_sku": normalize_seller_sku(variation_sku),
                }
            )

        if item_sku:
            records.append(
                {
                    **common_values,
                    "variation_id": "",
                    "seller_sku": item_sku,
                    "normalized_sku": normalize_seller_sku(item_sku),
                }
            )

    if not records:
        records.append(
            {
                **common_values,
                "variation_id": "",
                "seller_sku": item_sku,
                "normalized_sku": normalize_seller_sku(item_sku),
            }
        )

    return records


def extract_listing_record(
    item: dict[str, Any],
    *,
    company_code: str,
    seller_id: str,
    discovery_source: str,
    run_id: int,
    synced_at: datetime,
) -> dict[str, Any]:
    """Monta o registro de ml_listings a partir do detalhe do anúncio."""
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        raise ValueError("Detalhe de anuncio sem item_id.")

    tags = item.get("tags") if isinstance(item.get("tags"), list) else []
    shipping = item.get("shipping") if isinstance(item.get("shipping"), dict) else {}
    status = str(item.get("status") or "").strip().lower() or "unknown"
    catalog_listing = bool(item.get("catalog_listing"))
    family_id = item.get("family_id")
    parent_item_id = item.get("parent_item_id")
    catalog_product_id = item.get("catalog_product_id")
    user_product_id = item.get("user_product_id")

    return {
        "company_code": company_code.upper(),
        "seller_id": seller_id,
        "item_id": item_id,
        "title": str(item.get("title") or "").strip() or None,
        "permalink": str(item.get("permalink") or "").strip() or None,
        "status": status,
        "listing_type_id": str(item.get("listing_type_id") or "").strip() or None,
        "catalog_listing": catalog_listing,
        "catalog_product_id": (
            str(catalog_product_id).strip() if catalog_product_id is not None else None
        ),
        "catalog_boost": "catalog_boost" in tags,
        "user_product_id": (
            str(user_product_id).strip() if user_product_id is not None else None
        ),
        "family_id": str(family_id).strip() if family_id is not None else None,
        "parent_item_id": (
            str(parent_item_id).strip() if parent_item_id is not None else None
        ),
        "price": _to_decimal(item.get("price")),
        "base_price": _to_decimal(item.get("base_price")),
        "original_price": _to_decimal(item.get("original_price")),
        "currency_id": str(item.get("currency_id") or "").strip() or None,
        "available_quantity": _to_int(item.get("available_quantity")),
        "sold_quantity": _to_int(item.get("sold_quantity")),
        "condition": str(item.get("condition") or "").strip() or None,
        "channels": _json_list(item.get("channels")),
        "tags": _json_list(tags),
        "logistic_type": str(shipping.get("logistic_type") or "").strip() or None,
        "discovery_source": discovery_source,
        "is_active": status == "active",
        "ml_date_created": _parse_ml_datetime(item.get("date_created")),
        "ml_last_updated": _parse_ml_datetime(item.get("last_updated")),
        "last_seen_at": synced_at,
        "last_synced_at": synced_at,
        "last_sync_run_id": run_id,
    }


def extract_relation_records(
    item: dict[str, Any],
    *,
    company_code: str,
    seller_id: str,
    run_id: int,
    synced_at: datetime,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Extrai relações e os ITEM_IDs relacionados a enfileirar."""
    source_item_id = str(item.get("id") or "").strip()
    relations_raw = item.get("item_relations")
    if not source_item_id or not isinstance(relations_raw, list):
        return [], []

    records: list[dict[str, Any]] = []
    related_ids: list[str] = []
    for relation in relations_raw:
        if not isinstance(relation, dict):
            continue
        related_item_id = str(relation.get("id") or "").strip()
        if not related_item_id:
            continue
        variation_raw = relation.get("variation_id")
        related_variation_id = (
            str(variation_raw).strip() if variation_raw is not None else ""
        )
        stock_raw = relation.get("stock_relation")
        stock_relation = str(stock_raw).strip() if stock_raw is not None else None
        records.append(
            {
                "company_code": company_code.upper(),
                "seller_id": seller_id,
                "source_item_id": source_item_id,
                "related_item_id": related_item_id,
                "related_variation_id": related_variation_id,
                "stock_relation": stock_relation or None,
                "last_seen_at": synced_at,
                "last_sync_run_id": run_id,
            }
        )
        related_ids.append(related_item_id)
    return records, related_ids


# Compatibilidade com imports antigos (assinatura antiga sem listing_id).
def extract_listing_records(
    item: dict[str, Any],
    *,
    company_code: str,
    seller_id: str,
    run_id: int,
    synced_at: datetime,
) -> list[dict[str, Any]]:
    return extract_sku_records(
        item,
        company_code=company_code,
        seller_id=seller_id,
        listing_id=None,
        run_id=run_id,
        synced_at=synced_at,
    )


def run_ml_listing_sync(
    *,
    run_id: int,
    company_code: str,
    seller_id: str,
    access_token: str,
) -> None:
    """
    Pipeline completo: scan + catalog_boost + detalhes + relações + persistência.
    """
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")

    db = SessionLocal()
    repository = MLSyncRepository(db)
    items_processed = 0
    skus_found = 0
    items_without_sku = 0
    premium_count = 0
    classic_count = 0
    catalog_count = 0
    traditional_count = 0
    relations_found = 0
    errors_count = 0
    error_messages: list[str] = []

    def _persist_progress() -> None:
        repository.update_run(
            run_id,
            items_processed=items_processed,
            skus_found=skus_found,
            items_without_sku=items_without_sku,
            premium_count=premium_count,
            classic_count=classic_count,
            catalog_count=catalog_count,
            traditional_count=traditional_count,
            relations_found=relations_found,
            errors_count=errors_count,
        )

    try:
        scan_result = buscar_todos_itens_ativos_vendedor(access_token, seller_id)
        catalog_result = buscar_itens_catalog_boost_ativos(access_token, seller_id)

        queue: deque[tuple[str, str]] = deque()
        queued_ids: set[str] = set()
        visited_ids: set[str] = set()

        def enqueue(item_id: str, source: str) -> None:
            normalized = item_id.strip()
            if not normalized or normalized in visited_ids or normalized in queued_ids:
                return
            queued_ids.add(normalized)
            queue.append((normalized, source))

        for item_id in scan_result["results"]:
            enqueue(str(item_id), "scan")
        for item_id in catalog_result["results"]:
            enqueue(str(item_id), "catalog_boost")

        repository.update_run(run_id, items_found=len(queued_ids))

        while queue:
            batch_entries = [
                queue.popleft() for _ in range(min(DETAIL_BATCH_SIZE, len(queue)))
            ]
            batch_ids = [item_id for item_id, _ in batch_entries]
            source_by_id = {item_id: source for item_id, source in batch_entries}
            for item_id in batch_ids:
                visited_ids.add(item_id)
                queued_ids.discard(item_id)

            try:
                responses = obter_itens_em_lote(access_token, batch_ids)
            except ValueError as exc:
                errors_count += len(batch_ids)
                error_messages.append(str(exc))
                _persist_progress()
                continue

            listing_records: list[dict[str, Any]] = []
            sku_records_by_item: dict[str, list[dict[str, Any]]] = {}
            relation_records: list[dict[str, Any]] = []
            valid_responses = 0
            synced_at = datetime.now(UTC)

            response_by_id: dict[str, dict[str, Any]] = {}
            seen_response_ids: set[str] = set()
            for response in responses:
                if not isinstance(response, dict):
                    errors_count += 1
                    error_messages.append("Envelope invalido no multiget de itens.")
                    continue

                code = response.get("code")
                body = response.get("body")
                body_item_id = ""
                if isinstance(body, dict):
                    body_item_id = str(body.get("id") or "").strip()
                    if body_item_id:
                        seen_response_ids.add(body_item_id)

                if code != 200 or not isinstance(body, dict) or not body_item_id:
                    errors_count += 1
                    error_messages.append(f"Falha no detalhe de item. HTTP {code}.")
                    continue

                response_by_id[body_item_id] = body

            for item_id in batch_ids:
                body = response_by_id.get(item_id)
                if body is None:
                    if item_id not in seen_response_ids:
                        errors_count += 1
                        error_messages.append(
                            f"Multiget omitiu o item {item_id}."
                        )
                    continue

                discovery_source = source_by_id.get(item_id, "scan")
                try:
                    listing_record = extract_listing_record(
                        body,
                        company_code=company_code,
                        seller_id=seller_id,
                        discovery_source=discovery_source,
                        run_id=run_id,
                        synced_at=synced_at,
                    )
                    relations, related_ids = extract_relation_records(
                        body,
                        company_code=company_code,
                        seller_id=seller_id,
                        run_id=run_id,
                        synced_at=synced_at,
                    )
                    sku_records = extract_sku_records(
                        body,
                        company_code=company_code,
                        seller_id=seller_id,
                        listing_id=None,
                        run_id=run_id,
                        synced_at=synced_at,
                    )
                except ValueError as exc:
                    errors_count += 1
                    error_messages.append(str(exc))
                    continue

                listing_records.append(listing_record)
                sku_records_by_item[item_id] = sku_records
                relation_records.extend(relations)
                relations_found += len(relations)
                valid_responses += 1

                listing_type = listing_record.get("listing_type_id")
                if listing_type == "gold_pro":
                    premium_count += 1
                elif listing_type == "gold_special":
                    classic_count += 1

                if listing_record.get("catalog_listing"):
                    catalog_count += 1
                else:
                    traditional_count += 1

                if any(record["seller_sku"] for record in sku_records):
                    skus_found += sum(
                        1 for record in sku_records if record["seller_sku"]
                    )
                else:
                    items_without_sku += 1

                for related_id in related_ids:
                    enqueue(related_id, "relation")

            listing_id_by_item = repository.upsert_ml_listings(listing_records)
            sku_records_to_persist: list[dict[str, Any]] = []
            for item_id, sku_records in sku_records_by_item.items():
                listing_id = listing_id_by_item.get(item_id)
                for sku_record in sku_records:
                    sku_record["listing_id"] = listing_id
                    sku_records_to_persist.append(sku_record)

            repository.upsert_ml_listing_skus(sku_records_to_persist)
            repository.upsert_ml_listing_relations(relation_records)

            items_processed += valid_responses
            repository.update_run(
                run_id,
                items_found=len(visited_ids) + len(queue),
                items_processed=items_processed,
                skus_found=skus_found,
                items_without_sku=items_without_sku,
                premium_count=premium_count,
                classic_count=classic_count,
                catalog_count=catalog_count,
                traditional_count=traditional_count,
                relations_found=relations_found,
                errors_count=errors_count,
            )

        if errors_count == 0:
            repository.mark_unseen_as_inactive(
                company_code=company_code,
                seller_id=seller_id,
                run_id=run_id,
            )
            final_status = "completed"
        else:
            final_status = "completed_errors"

        repository.finish_run(
            run_id,
            status=final_status,
            finished_at=datetime.now(UTC),
            error_message=" | ".join(error_messages[:10]) or None,
        )
    except Exception as exc:
        repository.finish_run(
            run_id,
            status="failed",
            finished_at=datetime.now(UTC),
            error_message=str(exc),
        )
    finally:
        db.close()
