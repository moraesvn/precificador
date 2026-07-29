"""Baseline do esquema atual

Revision ID: 20260729_01
Revises:
Create Date: 2026-07-29 16:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260729_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("external_account_id", sa.String(length=100), nullable=True),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=True),
        sa.Column("token_type", sa.String(length=30), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_code",
            "provider",
            name="uq_company_provider",
        ),
    )
    op.create_index(
        "ix_oauth_connections_company_code",
        "oauth_connections",
        ["company_code"],
    )
    op.create_index(
        "ix_oauth_connections_provider",
        "oauth_connections",
        ["provider"],
    )

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state", sa.String(length=500), nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("code_verifier", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_oauth_states_company_code",
        "oauth_states",
        ["company_code"],
    )
    op.create_index(
        "ix_oauth_states_expires_at",
        "oauth_states",
        ["expires_at"],
    )
    op.create_index(
        "ix_oauth_states_provider",
        "oauth_states",
        ["provider"],
    )
    op.create_index(
        "ix_oauth_states_state",
        "oauth_states",
        ["state"],
        unique=True,
    )
    op.create_index(
        "ix_oauth_states_used_at",
        "oauth_states",
        ["used_at"],
    )

    op.create_table(
        "ml_sync_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("seller_id", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="running",
            nullable=False,
        ),
        sa.Column("items_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skus_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_without_sku", sa.Integer(), server_default="0", nullable=False),
        sa.Column("errors_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ml_sync_runs_company_started",
        "ml_sync_runs",
        ["company_code", "started_at"],
    )
    op.create_index(
        "ix_ml_sync_runs_seller_id",
        "ml_sync_runs",
        ["seller_id"],
    )
    op.create_index(
        "ix_ml_sync_runs_status",
        "ml_sync_runs",
        ["status"],
    )

    op.create_table(
        "ml_listing_skus",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("seller_id", sa.String(length=100), nullable=False),
        sa.Column("item_id", sa.String(length=100), nullable=False),
        sa.Column(
            "variation_id",
            sa.String(length=100),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column("seller_sku", sa.String(length=255), nullable=True),
        sa.Column("normalized_sku", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
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
            "variation_id",
            name="uq_ml_listing_sku_source",
        ),
    )
    op.create_index(
        "ix_ml_listing_skus_item",
        "ml_listing_skus",
        ["company_code", "seller_id", "item_id"],
    )
    op.create_index(
        "ix_ml_listing_skus_last_seen_at",
        "ml_listing_skus",
        ["last_seen_at"],
    )
    op.create_index(
        "ix_ml_listing_skus_last_sync_run_id",
        "ml_listing_skus",
        ["last_sync_run_id"],
    )
    op.create_index(
        "ix_ml_listing_skus_last_synced_at",
        "ml_listing_skus",
        ["last_synced_at"],
    )
    op.create_index(
        "ix_ml_listing_skus_match",
        "ml_listing_skus",
        ["company_code", "normalized_sku", "is_active"],
    )
    op.create_index(
        "ix_ml_listing_skus_status",
        "ml_listing_skus",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_ml_listing_skus_status", table_name="ml_listing_skus")
    op.drop_index("ix_ml_listing_skus_match", table_name="ml_listing_skus")
    op.drop_index("ix_ml_listing_skus_last_synced_at", table_name="ml_listing_skus")
    op.drop_index("ix_ml_listing_skus_last_sync_run_id", table_name="ml_listing_skus")
    op.drop_index("ix_ml_listing_skus_last_seen_at", table_name="ml_listing_skus")
    op.drop_index("ix_ml_listing_skus_item", table_name="ml_listing_skus")
    op.drop_table("ml_listing_skus")

    op.drop_index("ix_ml_sync_runs_status", table_name="ml_sync_runs")
    op.drop_index("ix_ml_sync_runs_seller_id", table_name="ml_sync_runs")
    op.drop_index("ix_ml_sync_runs_company_started", table_name="ml_sync_runs")
    op.drop_table("ml_sync_runs")

    op.drop_index("ix_oauth_states_used_at", table_name="oauth_states")
    op.drop_index("ix_oauth_states_state", table_name="oauth_states")
    op.drop_index("ix_oauth_states_provider", table_name="oauth_states")
    op.drop_index("ix_oauth_states_expires_at", table_name="oauth_states")
    op.drop_index("ix_oauth_states_company_code", table_name="oauth_states")
    op.drop_table("oauth_states")

    op.drop_index("ix_oauth_connections_provider", table_name="oauth_connections")
    op.drop_index("ix_oauth_connections_company_code", table_name="oauth_connections")
    op.drop_table("oauth_connections")
