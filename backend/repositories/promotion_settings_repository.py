from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.models import MarketplacePromotionSettings, PromotionTypeSetting
from backend.services.promotion_types_catalog import (
    DEFAULT_DISCOUNT_RULES,
    MVP_ENABLED_BY_DEFAULT,
    get_promotion_type_catalog,
)


class PromotionSettingsRepository:
    """Persistência das configs de promoção por empresa/marketplace."""

    def __init__(self, db: Session):
        self.db = db

    def get_marketplace_settings(
        self,
        *,
        company_code: str,
        marketplace: str,
    ) -> MarketplacePromotionSettings | None:
        return (
            self.db.query(MarketplacePromotionSettings)
            .filter(
                MarketplacePromotionSettings.company_code == company_code.upper(),
                MarketplacePromotionSettings.marketplace == marketplace.lower(),
            )
            .first()
        )

    def list_type_settings(
        self,
        *,
        company_code: str,
        marketplace: str,
    ) -> list[PromotionTypeSetting]:
        return (
            self.db.query(PromotionTypeSetting)
            .filter(
                PromotionTypeSetting.company_code == company_code.upper(),
                PromotionTypeSetting.marketplace == marketplace.lower(),
            )
            .order_by(PromotionTypeSetting.promotion_type)
            .all()
        )

    def ensure_defaults(
        self,
        *,
        company_code: str,
        marketplace: str,
    ) -> tuple[MarketplacePromotionSettings, list[PromotionTypeSetting]]:
        company = company_code.upper()
        market = marketplace.lower()

        marketplace_row = self.get_marketplace_settings(
            company_code=company, marketplace=market
        )
        if marketplace_row is None:
            marketplace_row = MarketplacePromotionSettings(
                company_code=company,
                marketplace=market,
                price_base_source="tiny",
                global_adjust_kind="percent",
                global_adjust_value=Decimal("0"),
            )
            self.db.add(marketplace_row)
            self.db.commit()
            self.db.refresh(marketplace_row)

        existing = {
            row.promotion_type: row
            for row in self.list_type_settings(company_code=company, marketplace=market)
        }
        created = False
        for catalog_item in get_promotion_type_catalog():
            code = str(catalog_item["code"])
            if code in existing:
                continue
            row = PromotionTypeSetting(
                company_code=company,
                marketplace=market,
                promotion_type=code,
                is_enabled=code in MVP_ENABLED_BY_DEFAULT,
                discount_rules=deepcopy(DEFAULT_DISCOUNT_RULES),
            )
            self.db.add(row)
            created = True
        if created:
            self.db.commit()

        type_rows = self.list_type_settings(company_code=company, marketplace=market)
        return marketplace_row, type_rows

    def update_marketplace_settings(
        self,
        *,
        company_code: str,
        marketplace: str,
        price_base_source: str | None = None,
        global_adjust_kind: str | None = None,
        global_adjust_value: Decimal | float | None = None,
    ) -> MarketplacePromotionSettings:
        self.ensure_defaults(company_code=company_code, marketplace=marketplace)
        values: dict[str, Any] = {"updated_at": func.now()}
        if price_base_source is not None:
            values["price_base_source"] = price_base_source
        if global_adjust_kind is not None:
            values["global_adjust_kind"] = global_adjust_kind
        if global_adjust_value is not None:
            values["global_adjust_value"] = global_adjust_value

        self.db.execute(
            update(MarketplacePromotionSettings)
            .where(
                MarketplacePromotionSettings.company_code == company_code.upper(),
                MarketplacePromotionSettings.marketplace == marketplace.lower(),
            )
            .values(**values)
        )
        self.db.commit()
        row = self.get_marketplace_settings(
            company_code=company_code, marketplace=marketplace
        )
        assert row is not None
        return row

    def upsert_type_setting(
        self,
        *,
        company_code: str,
        marketplace: str,
        promotion_type: str,
        is_enabled: bool | None = None,
        discount_rules: dict[str, Any] | None = None,
    ) -> PromotionTypeSetting:
        self.ensure_defaults(company_code=company_code, marketplace=marketplace)
        company = company_code.upper()
        market = marketplace.lower()
        code = promotion_type.strip().upper()

        values: dict[str, Any] = {
            "company_code": company,
            "marketplace": market,
            "promotion_type": code,
            "discount_rules": discount_rules or deepcopy(DEFAULT_DISCOUNT_RULES),
            "is_enabled": bool(is_enabled)
            if is_enabled is not None
            else code in MVP_ENABLED_BY_DEFAULT,
        }
        statement = insert(PromotionTypeSetting).values(**values)
        excluded = statement.excluded
        set_values: dict[str, Any] = {"updated_at": func.now()}
        if is_enabled is not None:
            set_values["is_enabled"] = excluded.is_enabled
        if discount_rules is not None:
            set_values["discount_rules"] = excluded.discount_rules
        statement = statement.on_conflict_do_update(
            constraint="uq_promotion_type_settings",
            set_=set_values,
        )
        self.db.execute(statement)
        self.db.commit()

        row = (
            self.db.query(PromotionTypeSetting)
            .filter(
                PromotionTypeSetting.company_code == company,
                PromotionTypeSetting.marketplace == market,
                PromotionTypeSetting.promotion_type == code,
            )
            .first()
        )
        assert row is not None
        return row
