from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.models import MLListing, MLListingRelation, MLListingSku, MLSyncRun


def _normalize_seller_sku(value: str | None) -> str | None:
    normalized = (value or "").strip().upper()
    return normalized or None


class MLSyncRepository:
    """Persistência do catálogo ML (listings, SKUs, relações) e histórico de sync."""

    def __init__(self, db: Session):
        self.db = db

    def create_run(self, company_code: str, seller_id: str) -> MLSyncRun:
        run = MLSyncRun(
            company_code=company_code.upper(),
            seller_id=seller_id,
            status="running",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: int) -> MLSyncRun | None:
        return self.db.query(MLSyncRun).filter(MLSyncRun.id == run_id).first()

    def get_running_run(
        self,
        *,
        company_code: str,
        seller_id: str,
    ) -> MLSyncRun | None:
        return (
            self.db.query(MLSyncRun)
            .filter(
                MLSyncRun.company_code == company_code.upper(),
                MLSyncRun.seller_id == seller_id,
                MLSyncRun.status == "running",
            )
            .order_by(MLSyncRun.id.desc())
            .first()
        )

    def update_run(self, run_id: int, **values: Any) -> None:
        self.db.execute(
            update(MLSyncRun).where(MLSyncRun.id == run_id).values(**values)
        )
        self.db.commit()

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        finished_at: datetime,
        error_message: str | None = None,
    ) -> None:
        self.update_run(
            run_id,
            status=status,
            finished_at=finished_at,
            error_message=error_message,
        )

    def upsert_ml_listings(self, records: list[dict[str, Any]]) -> dict[str, int]:
        """Insere/atualiza anúncios e retorna mapa item_id → listing.id."""
        if not records:
            return {}

        statement = insert(MLListing).values(records)
        excluded = statement.excluded
        statement = statement.on_conflict_do_update(
            constraint="uq_ml_listing_item",
            set_={
                "title": excluded.title,
                "permalink": excluded.permalink,
                "status": excluded.status,
                "listing_type_id": excluded.listing_type_id,
                "catalog_listing": excluded.catalog_listing,
                "catalog_product_id": excluded.catalog_product_id,
                "catalog_boost": excluded.catalog_boost,
                "user_product_id": excluded.user_product_id,
                "family_id": excluded.family_id,
                "parent_item_id": excluded.parent_item_id,
                "price": excluded.price,
                "base_price": excluded.base_price,
                "original_price": excluded.original_price,
                "currency_id": excluded.currency_id,
                "available_quantity": excluded.available_quantity,
                "sold_quantity": excluded.sold_quantity,
                "condition": excluded.condition,
                "channels": excluded.channels,
                "tags": excluded.tags,
                "logistic_type": excluded.logistic_type,
                "is_active": excluded.is_active,
                "ml_date_created": excluded.ml_date_created,
                "ml_last_updated": excluded.ml_last_updated,
                "last_seen_at": excluded.last_seen_at,
                "last_synced_at": excluded.last_synced_at,
                "last_sync_run_id": excluded.last_sync_run_id,
                "updated_at": func.now(),
            },
        ).returning(MLListing.id, MLListing.item_id)
        rows = self.db.execute(statement).all()
        self.db.commit()
        return {str(item_id): int(listing_id) for listing_id, item_id in rows}

    def upsert_ml_listing_skus(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return

        statement = insert(MLListingSku).values(records)
        excluded = statement.excluded
        statement = statement.on_conflict_do_update(
            constraint="uq_ml_listing_sku_source",
            set_={
                "listing_id": excluded.listing_id,
                "seller_sku": excluded.seller_sku,
                "normalized_sku": excluded.normalized_sku,
                "title": excluded.title,
                "status": excluded.status,
                "is_active": excluded.is_active,
                "ml_last_updated": excluded.ml_last_updated,
                "last_seen_at": excluded.last_seen_at,
                "last_synced_at": excluded.last_synced_at,
                "last_sync_run_id": excluded.last_sync_run_id,
                "updated_at": func.now(),
            },
        )
        self.db.execute(statement)
        self.db.commit()

    def upsert_ml_listing_relations(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return

        statement = insert(MLListingRelation).values(records)
        excluded = statement.excluded
        statement = statement.on_conflict_do_update(
            constraint="uq_ml_listing_relation",
            set_={
                "stock_relation": excluded.stock_relation,
                "last_seen_at": excluded.last_seen_at,
                "last_sync_run_id": excluded.last_sync_run_id,
                "updated_at": func.now(),
            },
        )
        self.db.execute(statement)
        self.db.commit()

    def mark_unseen_as_inactive(
        self,
        *,
        company_code: str,
        seller_id: str,
        run_id: int,
    ) -> dict[str, int]:
        """Inativa listings e SKUs não vistos nesta execução bem-sucedida."""
        company = company_code.upper()
        listings_result = self.db.execute(
            update(MLListing)
            .where(
                MLListing.company_code == company,
                MLListing.seller_id == seller_id,
                MLListing.is_active.is_(True),
                or_(
                    MLListing.last_sync_run_id.is_(None),
                    MLListing.last_sync_run_id != run_id,
                ),
            )
            .values(is_active=False, updated_at=func.now())
        )
        skus_result = self.db.execute(
            update(MLListingSku)
            .where(
                MLListingSku.company_code == company,
                MLListingSku.seller_id == seller_id,
                MLListingSku.is_active.is_(True),
                or_(
                    MLListingSku.last_sync_run_id.is_(None),
                    MLListingSku.last_sync_run_id != run_id,
                ),
            )
            .values(is_active=False, updated_at=func.now())
        )
        self.db.commit()
        return {
            "listings": int(listings_result.rowcount or 0),
            "skus": int(skus_result.rowcount or 0),
        }

    def list_entries(
        self,
        *,
        company_code: str,
        active_only: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[MLListingSku], int]:
        query = self.db.query(MLListingSku).filter(
            MLListingSku.company_code == company_code.upper()
        )
        if active_only:
            query = query.filter(MLListingSku.is_active.is_(True))

        total = query.count()
        entries = (
            query.order_by(MLListingSku.item_id, MLListingSku.variation_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return entries, total

    def list_listings(
        self,
        *,
        company_code: str,
        active_only: bool,
        catalog_listing: bool | None,
        listing_type_id: str | None,
        discovery_source: str | None,
        catalog_boost: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[MLListing], int]:
        query = self.db.query(MLListing).filter(
            MLListing.company_code == company_code.upper()
        )
        if active_only:
            query = query.filter(MLListing.is_active.is_(True))
        if catalog_listing is not None:
            query = query.filter(MLListing.catalog_listing.is_(catalog_listing))
        if listing_type_id:
            query = query.filter(MLListing.listing_type_id == listing_type_id)
        if discovery_source:
            query = query.filter(MLListing.discovery_source == discovery_source)
        if catalog_boost is not None:
            query = query.filter(MLListing.catalog_boost.is_(catalog_boost))

        total = query.count()
        entries = (
            query.order_by(MLListing.item_id).offset(offset).limit(limit).all()
        )
        return entries, total

    def list_relations(
        self,
        *,
        company_code: str,
        item_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[MLListingRelation], int]:
        query = self.db.query(MLListingRelation).filter(
            MLListingRelation.company_code == company_code.upper()
        )
        if item_id:
            normalized = item_id.strip()
            query = query.filter(
                or_(
                    MLListingRelation.source_item_id == normalized,
                    MLListingRelation.related_item_id == normalized,
                )
            )

        total = query.count()
        entries = (
            query.order_by(
                MLListingRelation.source_item_id,
                MLListingRelation.related_item_id,
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
        return entries, total

    def find_offers_by_sku(
        self,
        *,
        company_code: str,
        sku: str,
        active_only: bool,
    ) -> list[tuple[MLListingSku, MLListing | None]]:
        """Retorna SKUs do catálogo local com o anúncio associado (se houver)."""
        normalized = _normalize_seller_sku(sku)
        if not normalized:
            return []

        query = (
            self.db.query(MLListingSku, MLListing)
            .outerjoin(MLListing, MLListingSku.listing_id == MLListing.id)
            .filter(
                MLListingSku.company_code == company_code.upper(),
                MLListingSku.normalized_sku == normalized,
            )
        )
        if active_only:
            query = query.filter(MLListingSku.is_active.is_(True))

        return query.order_by(MLListingSku.item_id, MLListingSku.variation_id).all()

    def list_relations_for_items(
        self,
        *,
        company_code: str,
        item_ids: list[str],
    ) -> list[MLListingRelation]:
        if not item_ids:
            return []
        return (
            self.db.query(MLListingRelation)
            .filter(
                MLListingRelation.company_code == company_code.upper(),
                or_(
                    MLListingRelation.source_item_id.in_(item_ids),
                    MLListingRelation.related_item_id.in_(item_ids),
                ),
            )
            .order_by(
                MLListingRelation.source_item_id,
                MLListingRelation.related_item_id,
            )
            .all()
        )
