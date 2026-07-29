from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.ml_auth import get_ml_connection_with_optional_refresh
from backend.models import MLListingSku, MLSyncRun
from backend.repositories.ml_sync_repository import MLSyncRepository
from backend.services.ml_api_service import obter_usuario_autenticado
from backend.services.ml_listing_sync_service import run_ml_listing_sync


router = APIRouter(prefix="/ml", tags=["ml-sync"])


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


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


def _serialize_listing(entry: MLListingSku) -> dict:
    return {
        "company_code": entry.company_code,
        "seller_id": entry.seller_id,
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
    """Inicia em segundo plano a sincronização dos anúncios ativos e seus SKUs."""
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
    """Lista a primeira versão persistida do relacionamento SKU x anúncio ML."""
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
        "results": [_serialize_listing(entry) for entry in entries],
    }
