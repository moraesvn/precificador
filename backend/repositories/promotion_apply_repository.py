"""Persistência de runs/itens de apply de promoção."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.models import PromotionApplyItem, PromotionApplyRun


class PromotionApplyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        *,
        company_code: str,
        marketplace: str,
        promotion_type: str,
        campaign_name: str | None,
        start_date: str | None,
        finish_date: str | None,
        ml_promotion_id: str | None,
        dry_run: bool,
        items_total: int,
        status: str = "running",
    ) -> PromotionApplyRun:
        run = PromotionApplyRun(
            company_code=company_code.upper(),
            marketplace=marketplace,
            promotion_type=promotion_type,
            campaign_name=campaign_name,
            start_date=start_date,
            finish_date=finish_date,
            ml_promotion_id=ml_promotion_id,
            dry_run=dry_run,
            items_total=items_total,
            status=status,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_run(
        self,
        run: PromotionApplyRun,
        *,
        ml_promotion_id: str | None = None,
        status: str | None = None,
        items_success: int | None = None,
        items_failed: int | None = None,
        items_skipped: int | None = None,
        error_message: str | None = None,
        finished: bool = False,
    ) -> PromotionApplyRun:
        if ml_promotion_id is not None:
            run.ml_promotion_id = ml_promotion_id
        if status is not None:
            run.status = status
        if items_success is not None:
            run.items_success = items_success
        if items_failed is not None:
            run.items_failed = items_failed
        if items_skipped is not None:
            run.items_skipped = items_skipped
        if error_message is not None:
            run.error_message = error_message
        if finished:
            run.finished_at = datetime.now(UTC)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def add_item(
        self,
        *,
        run_id: int,
        item_id: str,
        sku: str | None,
        deal_price: float | None,
        status: str,
        http_status: int | None = None,
        response_body: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> PromotionApplyItem:
        row = PromotionApplyItem(
            run_id=run_id,
            item_id=item_id,
            sku=sku,
            deal_price=deal_price,
            status=status,
            http_status=http_status,
            response_body=response_body,
            error_message=error_message,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_run(self, run_id: int, *, company_code: str) -> PromotionApplyRun | None:
        return (
            self.db.query(PromotionApplyRun)
            .filter(
                PromotionApplyRun.id == run_id,
                PromotionApplyRun.company_code == company_code.upper(),
            )
            .first()
        )

    def list_items(self, run_id: int) -> list[PromotionApplyItem]:
        return (
            self.db.query(PromotionApplyItem)
            .filter(PromotionApplyItem.run_id == run_id)
            .order_by(PromotionApplyItem.id)
            .all()
        )
