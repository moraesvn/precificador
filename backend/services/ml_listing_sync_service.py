from datetime import UTC, datetime
from typing import Any

from backend.db import SessionLocal
from backend.repositories.ml_sync_repository import MLSyncRepository
from backend.services.ml_api_service import (
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


def extract_listing_records(
    item: dict[str, Any],
    *,
    company_code: str,
    seller_id: str,
    run_id: int,
    synced_at: datetime,
) -> list[dict[str, Any]]:
    """Converte o detalhe de um anúncio em registros por item/variação."""
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        raise ValueError("Detalhe de anuncio sem item_id.")

    title = str(item.get("title") or "").strip() or None
    status = str(item.get("status") or "").strip().lower() or "unknown"
    is_active = status == "active"
    ml_last_updated = _parse_ml_datetime(item.get("last_updated"))
    item_sku = _get_seller_sku(item.get("attributes"))
    common_values = {
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


def _chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def run_ml_listing_sync(
    *,
    run_id: int,
    company_code: str,
    seller_id: str,
    access_token: str,
) -> None:
    """Executa scan, consulta detalhes e persiste o índice SKU x MLB."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada.")

    db = SessionLocal()
    repository = MLSyncRepository(db)
    items_processed = 0
    skus_found = 0
    items_without_sku = 0
    errors_count = 0
    error_messages: list[str] = []

    try:
        scan_result = buscar_todos_itens_ativos_vendedor(access_token, seller_id)
        item_ids = scan_result["results"]
        repository.update_run(run_id, items_found=len(item_ids))

        for item_id_batch in _chunks(item_ids, DETAIL_BATCH_SIZE):
            try:
                responses = obter_itens_em_lote(access_token, item_id_batch)
            except ValueError as exc:
                errors_count += len(item_id_batch)
                error_messages.append(str(exc))
                repository.update_run(
                    run_id,
                    items_processed=items_processed,
                    skus_found=skus_found,
                    items_without_sku=items_without_sku,
                    errors_count=errors_count,
                )
                continue

            records: list[dict[str, Any]] = []
            valid_responses = 0
            for response in responses:
                if not isinstance(response, dict):
                    errors_count += 1
                    error_messages.append("Envelope invalido no multiget de itens.")
                    continue

                code = response.get("code")
                body = response.get("body")
                if code != 200 or not isinstance(body, dict):
                    errors_count += 1
                    error_messages.append(f"Falha no detalhe de item. HTTP {code}.")
                    continue

                try:
                    item_records = extract_listing_records(
                        body,
                        company_code=company_code,
                        seller_id=seller_id,
                        run_id=run_id,
                        synced_at=datetime.now(UTC),
                    )
                except ValueError as exc:
                    errors_count += 1
                    error_messages.append(str(exc))
                    continue

                records.extend(item_records)
                valid_responses += 1
                if any(record["seller_sku"] for record in item_records):
                    skus_found += sum(
                        1 for record in item_records if record["seller_sku"]
                    )
                else:
                    items_without_sku += 1

            missing_responses = max(0, len(item_id_batch) - len(responses))
            if missing_responses:
                errors_count += missing_responses
                error_messages.append(
                    f"Multiget omitiu {missing_responses} resposta(s) do lote."
                )

            repository.upsert_listings(records)
            items_processed += valid_responses
            repository.update_run(
                run_id,
                items_processed=items_processed,
                skus_found=skus_found,
                items_without_sku=items_without_sku,
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
