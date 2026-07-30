from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.ml_auth import get_ml_connection_with_optional_refresh
from backend.models import MLListing, MLListingRelation, MLListingSku, MLSyncRun
from backend.repositories.ml_sync_repository import MLSyncRepository
from backend.services.ml_api_service import obter_usuario_autenticado
from backend.services.ml_listing_sync_service import run_ml_listing_sync


router = APIRouter(prefix="/ml", tags=["ml-sync"])


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _number_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _exposure_label(listing_type_id: str | None) -> str | None:
    mapping = {
        "gold_pro": "Premium",
        "gold_special": "Clássico",
        "free": "Grátis",
    }
    if not listing_type_id:
        return None
    return mapping.get(listing_type_id, listing_type_id)


def _serialize_run(run: MLSyncRun) -> dict:
    return {
        "id": run.id,
        "company_code": run.company_code,
        "seller_id": run.seller_id,
        "status": run.status,
        "items_found": run.items_found,
        "items_processed": run.items_processed,
        "skus_found": run.skus_found,
        "items_without_sku": run.items_without_sku,
        "premium_count": run.premium_count,
        "classic_count": run.classic_count,
        "catalog_count": run.catalog_count,
        "traditional_count": run.traditional_count,
        "relations_found": run.relations_found,
        "errors_count": run.errors_count,
        "error_message": run.error_message,
        "started_at": _iso_or_none(run.started_at),
        "finished_at": _iso_or_none(run.finished_at),
    }


def _serialize_sku_row(entry: MLListingSku) -> dict:
    return {
        "company_code": entry.company_code,
        "seller_id": entry.seller_id,
        "listing_id": entry.listing_id,
        "item_id": entry.item_id,
        "variation_id": entry.variation_id or None,
        "seller_sku": entry.seller_sku,
        "normalized_sku": entry.normalized_sku,
        "title": entry.title,
        "status": entry.status,
        "is_active": entry.is_active,
        "ml_last_updated": _iso_or_none(entry.ml_last_updated),
        "last_seen_at": _iso_or_none(entry.last_seen_at),
        "last_synced_at": _iso_or_none(entry.last_synced_at),
    }


def _serialize_ml_listing(entry: MLListing) -> dict:
    return {
        "id": entry.id,
        "company_code": entry.company_code,
        "seller_id": entry.seller_id,
        "item_id": entry.item_id,
        "title": entry.title,
        "permalink": entry.permalink,
        "status": entry.status,
        "listing_type_id": entry.listing_type_id,
        "exposure": _exposure_label(entry.listing_type_id),
        "catalog_listing": entry.catalog_listing,
        "catalog_product_id": entry.catalog_product_id,
        "catalog_boost": entry.catalog_boost,
        "price": _number_or_none(entry.price),
        "base_price": _number_or_none(entry.base_price),
        "original_price": _number_or_none(entry.original_price),
        "currency_id": entry.currency_id,
        "available_quantity": entry.available_quantity,
        "sold_quantity": entry.sold_quantity,
        "condition": entry.condition,
        "logistic_type": entry.logistic_type,
        "discovery_source": entry.discovery_source,
        "is_active": entry.is_active,
        "ml_date_created": _iso_or_none(entry.ml_date_created),
        "ml_last_updated": _iso_or_none(entry.ml_last_updated),
        "last_synced_at": _iso_or_none(entry.last_synced_at),
    }


def _serialize_relation(entry: MLListingRelation) -> dict:
    return {
        "id": entry.id,
        "company_code": entry.company_code,
        "seller_id": entry.seller_id,
        "source_item_id": entry.source_item_id,
        "related_item_id": entry.related_item_id,
        "related_variation_id": entry.related_variation_id or None,
        "stock_relation": entry.stock_relation,
        "last_seen_at": _iso_or_none(entry.last_seen_at),
        "last_sync_run_id": entry.last_sync_run_id,
    }


@router.post("/catalog-sync", status_code=202)
def start_catalog_sync(
    background_tasks: BackgroundTasks,
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Inicia em segundo plano o pipeline completo do catálogo ML.

    Inclui scan de ativos, tag catalog_boost, detalhes em lote, item_relations
    e persistência em ml_listings / ml_listing_skus / ml_listing_relations.
    """
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    company_code = connection.company_code.upper()
    seller_id = (connection.external_account_id or "").strip()

    try:
        if not seller_id:
            profile = obter_usuario_autenticado(connection.access_token)
            seller_id = str(profile.get("id") or "").strip()
        if not seller_id:
            raise ValueError("Nao foi possivel obter user_id do Mercado Livre.")
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    repository = MLSyncRepository(db)
    running = repository.get_running_run(
        company_code=company_code,
        seller_id=seller_id,
    )
    if running is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Ja existe uma sincronizacao em andamento.",
                "run_id": running.id,
            },
        )

    run = repository.create_run(company_code, seller_id)
    background_tasks.add_task(
        run_ml_listing_sync,
        run_id=run.id,
        company_code=company_code,
        seller_id=seller_id,
        access_token=connection.access_token,
    )
    return _serialize_run(run)


@router.get("/catalog-sync/{run_id}")
def get_catalog_sync_status(
    run_id: int,
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Consulta progresso e resultado de uma sincronização."""
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    repository = MLSyncRepository(db)
    run = repository.get_run(run_id)
    if run is None or run.company_code != connection.company_code.upper():
        raise HTTPException(status_code=404, detail="Sincronizacao nao encontrada.")
    return _serialize_run(run)


@router.get("/sku-map")
def list_ml_sku_map(
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    active_only: bool = Query(default=True, description="Retornar apenas registros ativos"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Lista o relacionamento SKU x anúncio ML."""
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    repository = MLSyncRepository(db)
    entries, total = repository.list_entries(
        company_code=connection.company_code,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return {
        "paging": {"total": total, "limit": limit, "offset": offset},
        "results": [_serialize_sku_row(entry) for entry in entries],
    }


@router.get("/listings")
def list_ml_listings(
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    active_only: bool = Query(default=True),
    catalog_listing: bool | None = Query(
        default=None,
        description="Filtrar catálogo (true) ou tradicional (false)",
    ),
    listing_type_id: str | None = Query(
        default=None,
        description="Ex.: gold_pro (Premium) ou gold_special (Clássico)",
    ),
    discovery_source: str | None = Query(
        default=None,
        description="scan | catalog_boost | relation",
    ),
    catalog_boost: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Lista anúncios persistidos em ml_listings."""
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    repository = MLSyncRepository(db)
    entries, total = repository.list_listings(
        company_code=connection.company_code,
        active_only=active_only,
        catalog_listing=catalog_listing,
        listing_type_id=(listing_type_id or "").strip() or None,
        discovery_source=(discovery_source or "").strip() or None,
        catalog_boost=catalog_boost,
        limit=limit,
        offset=offset,
    )
    return {
        "paging": {"total": total, "limit": limit, "offset": offset},
        "results": [_serialize_ml_listing(entry) for entry in entries],
    }


@router.get("/listing-relations")
def list_ml_listing_relations(
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    item_id: str | None = Query(
        default=None,
        description="Filtrar relações onde o MLB é origem ou destino",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Lista relações tradicional ↔ catálogo persistidas."""
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    repository = MLSyncRepository(db)
    entries, total = repository.list_relations(
        company_code=connection.company_code,
        item_id=(item_id or "").strip() or None,
        limit=limit,
        offset=offset,
    )
    return {
        "paging": {"total": total, "limit": limit, "offset": offset},
        "results": [_serialize_relation(entry) for entry in entries],
    }


@router.get("/sku-offers")
def get_ml_sku_offers(
    sku: str = Query(..., description="SELLER_SKU a consultar (ex.: 4063)"),
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    active_only: bool = Query(default=True),
    x_internal_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Agrupa todas as ofertas ML de um SKU, com classificação e relações."""
    connection = get_ml_connection_with_optional_refresh(db, company, x_internal_token)
    repository = MLSyncRepository(db)
    pairs = repository.find_offers_by_sku(
        company_code=connection.company_code,
        sku=sku,
        active_only=active_only,
    )
    item_ids = [sku_row.item_id for sku_row, _ in pairs]
    relations = repository.list_relations_for_items(
        company_code=connection.company_code,
        item_ids=item_ids,
    )

    offers = []
    for sku_row, listing in pairs:
        offer = {
            **_serialize_sku_row(sku_row),
            "listing": _serialize_ml_listing(listing) if listing is not None else None,
        }
        offers.append(offer)

    return {
        "sku": sku.strip(),
        "offers_count": len(offers),
        "offers": offers,
        "relations": [_serialize_relation(rel) for rel in relations],
    }
