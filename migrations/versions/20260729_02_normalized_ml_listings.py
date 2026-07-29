"""Modelo normalizado de anúncios ML

Revision ID: 20260729_02
Revises: 20260729_01
Create Date: 2026-07-29 16:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260729_02"
down_revision: str | None = "20260729_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ml_sync_runs",
        sa.Column("premium_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ml_sync_runs",
        sa.Column("classic_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ml_sync_runs",
        sa.Column("catalog_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ml_sync_runs",
        sa.Column("traditional_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "ml_sync_runs",
        sa.Column("relations_found", sa.Integer(), server_default="0", nullable=False),
    )

    op.create_table(
        "ml_listings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("seller_id", sa.String(length=100), nullable=False),
        sa.Column("item_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("permalink", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("listing_type_id", sa.String(length=50), nullable=True),
        sa.Column(
            "catalog_listing",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("catalog_product_id", sa.String(length=100), nullable=True),
        sa.Column(
            "catalog_boost",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("user_product_id", sa.String(length=100), nullable=True),
        sa.Column("family_id", sa.String(length=100), nullable=True),
        sa.Column("parent_item_id", sa.String(length=100), nullable=True),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("base_price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("original_price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("currency_id", sa.String(length=10), nullable=True),
        sa.Column("available_quantity", sa.Integer(), nullable=True),
        sa.Column("sold_quantity", sa.Integer(), nullable=True),
        sa.Column("condition", sa.String(length=30), nullable=True),
        sa.Column("channels", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("logistic_type", sa.String(length=50), nullable=True),
        sa.Column(
            "discovery_source",
            sa.String(length=30),
            server_default="scan",
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("ml_date_created", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ml_last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync_run_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["last_sync_run_id"],
            ["ml_sync_runs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_code",
            "seller_id",
            "item_id",
            name="uq_ml_listing_item",
        ),
    )
    op.create_index(
        "ix_ml_listings_status",
        "ml_listings",
        ["company_code", "seller_id", "status", "is_active"],
    )
    op.create_index(
        "ix_ml_listings_catalog",
        "ml_listings",
        ["company_code", "seller_id", "catalog_listing", "is_active"],
    )
    op.create_index(
        "ix_ml_listings_listing_type",
        "ml_listings",
        ["company_code", "seller_id", "listing_type_id"],
    )
    op.create_index("ix_ml_listings_status_col", "ml_listings", ["status"])
    op.create_index("ix_ml_listings_last_seen_at", "ml_listings", ["last_seen_at"])
    op.create_index("ix_ml_listings_last_synced_at", "ml_listings", ["last_synced_at"])
    op.create_index(
        "ix_ml_listings_last_sync_run_id",
        "ml_listings",
        ["last_sync_run_id"],
    )

    op.create_table(
        "ml_listing_relations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("seller_id", sa.String(length=100), nullable=False),
        sa.Column("source_item_id", sa.String(length=100), nullable=False),
        sa.Column("related_item_id", sa.String(length=100), nullable=False),
        sa.Column(
            "related_variation_id",
            sa.String(length=100),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("stock_relation", sa.String(length=50), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync_run_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["last_sync_run_id"],
            ["ml_sync_runs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_code",
            "seller_id",
            "source_item_id",
            "related_item_id",
            "related_variation_id",
            name="uq_ml_listing_relation",
        ),
    )
    op.create_index(
        "ix_ml_listing_relations_source",
        "ml_listing_relations",
        ["company_code", "seller_id", "source_item_id"],
    )
    op.create_index(
        "ix_ml_listing_relations_related",
        "ml_listing_relations",
        ["company_code", "seller_id", "related_item_id"],
    )
    op.create_index(
        "ix_ml_listing_relations_last_seen_at",
        "ml_listing_relations",
        ["last_seen_at"],
    )
    op.create_index(
        "ix_ml_listing_relations_last_sync_run_id",
        "ml_listing_relations",
        ["last_sync_run_id"],
    )

    op.add_column(
        "ml_listing_skus",
        sa.Column("listing_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_ml_listing_skus_listing_id",
        "ml_listing_skus",
        "ml_listings",
        ["listing_id"],
        ["id"],
    )
    op.create_index(
        "ix_ml_listing_skus_listing_id",
        "ml_listing_skus",
        ["listing_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ml_listing_skus_listing_id", table_name="ml_listing_skus")
    op.drop_constraint(
        "fk_ml_listing_skus_listing_id",
        "ml_listing_skus",
        type_="foreignkey",
    )
    op.drop_column("ml_listing_skus", "listing_id")

    op.drop_index(
        "ix_ml_listing_relations_last_sync_run_id",
        table_name="ml_listing_relations",
    )
    op.drop_index(
        "ix_ml_listing_relations_last_seen_at",
        table_name="ml_listing_relations",
    )
    op.drop_index(
        "ix_ml_listing_relations_related",
        table_name="ml_listing_relations",
    )
    op.drop_index(
        "ix_ml_listing_relations_source",
        table_name="ml_listing_relations",
    )
    op.drop_table("ml_listing_relations")

    op.drop_index("ix_ml_listings_last_sync_run_id", table_name="ml_listings")
    op.drop_index("ix_ml_listings_last_synced_at", table_name="ml_listings")
    op.drop_index("ix_ml_listings_last_seen_at", table_name="ml_listings")
    op.drop_index("ix_ml_listings_status_col", table_name="ml_listings")
    op.drop_index("ix_ml_listings_listing_type", table_name="ml_listings")
    op.drop_index("ix_ml_listings_catalog", table_name="ml_listings")
    op.drop_index("ix_ml_listings_status", table_name="ml_listings")
    op.drop_table("ml_listings")

    op.drop_column("ml_sync_runs", "relations_found")
    op.drop_column("ml_sync_runs", "traditional_count")
    op.drop_column("ml_sync_runs", "catalog_count")
    op.drop_column("ml_sync_runs", "classic_count")
    op.drop_column("ml_sync_runs", "premium_count")
