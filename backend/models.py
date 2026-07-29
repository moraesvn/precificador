from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class OAuthConnection(Base):
    __tablename__ = "oauth_connections"
    __table_args__ = (
        UniqueConstraint("company_code", "provider", name="uq_company_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    external_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    scope: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_verifier: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MLSyncRun(Base):
    """Registra cada tentativa de sincronização dos anúncios do Mercado Livre."""

    __tablename__ = "ml_sync_runs"
    __table_args__ = (
        Index("ix_ml_sync_runs_company_started", "company_code", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running", server_default="running", index=True
    )
    items_found: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    items_processed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    skus_found: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    items_without_sku: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    premium_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    classic_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    catalog_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    traditional_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    relations_found: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    errors_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class MLListing(Base):
    """Uma linha por ITEM_ID do Mercado Livre (anúncio tradicional ou de catálogo)."""

    __tablename__ = "ml_listings"
    __table_args__ = (
        UniqueConstraint(
            "company_code",
            "seller_id",
            "item_id",
            name="uq_ml_listing_item",
        ),
        Index(
            "ix_ml_listings_status",
            "company_code",
            "seller_id",
            "status",
            "is_active",
        ),
        Index(
            "ix_ml_listings_catalog",
            "company_code",
            "seller_id",
            "catalog_listing",
            "is_active",
        ),
        Index(
            "ix_ml_listings_listing_type",
            "company_code",
            "seller_id",
            "listing_type_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(100), nullable=False)
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    permalink: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    listing_type_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    catalog_listing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    catalog_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    catalog_boost: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    user_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    family_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_item_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    base_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    original_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    available_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sold_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    condition: Mapped[str | None] = mapped_column(String(30), nullable=True)
    channels: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    logistic_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Origem da descoberta: scan | catalog_boost | relation
    discovery_source: Mapped[str] = mapped_column(
        String(30), nullable=False, default="scan", server_default="scan"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    ml_date_created: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ml_last_updated: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_synced_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_sync_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_sync_runs.id"), nullable=True, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MLListingRelation(Base):
    """Relação entre anúncios (ex.: tradicional ↔ catálogo via item_relations)."""

    __tablename__ = "ml_listing_relations"
    __table_args__ = (
        UniqueConstraint(
            "company_code",
            "seller_id",
            "source_item_id",
            "related_item_id",
            "related_variation_id",
            name="uq_ml_listing_relation",
        ),
        Index(
            "ix_ml_listing_relations_source",
            "company_code",
            "seller_id",
            "source_item_id",
        ),
        Index(
            "ix_ml_listing_relations_related",
            "company_code",
            "seller_id",
            "related_item_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    related_item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # String vazia quando a relação não aponta para uma variação específica.
    related_variation_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="", server_default=""
    )
    stock_relation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_seen_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_sync_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_sync_runs.id"), nullable=True, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MLListingSku(Base):
    """Relacionamento entre anúncio (ou variação) e SELLER_SKU."""

    __tablename__ = "ml_listing_skus"
    __table_args__ = (
        UniqueConstraint(
            "company_code",
            "seller_id",
            "item_id",
            "variation_id",
            name="uq_ml_listing_sku_source",
        ),
        Index(
            "ix_ml_listing_skus_match",
            "company_code",
            "normalized_sku",
            "is_active",
        ),
        Index(
            "ix_ml_listing_skus_item",
            "company_code",
            "seller_id",
            "item_id",
        ),
        Index(
            "ix_ml_listing_skus_listing_id",
            "listing_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # FK preenchida pelo sincronizador normalizado; nullable até a etapa do sync completo.
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_listings.id"), nullable=True, index=True
    )
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(100), nullable=False)
    item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # String vazia representa o SKU no nível do anúncio, sem variação.
    variation_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="", server_default=""
    )
    seller_sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Campos espelhados do anúncio: mantidos até o sync passar a usar ml_listings.
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    ml_last_updated: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_synced_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_sync_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_sync_runs.id"), nullable=True, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
