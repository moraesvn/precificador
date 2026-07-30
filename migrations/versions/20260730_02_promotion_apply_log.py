"""Log de apply de promoções

Revision ID: 20260730_02
Revises: 20260730_01
Create Date: 2026-07-30 16:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260730_02"
down_revision: str | None = "20260730_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "promotion_apply_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("marketplace", sa.String(length=30), nullable=False),
        sa.Column("promotion_type", sa.String(length=50), nullable=False),
        sa.Column("ml_promotion_id", sa.String(length=100), nullable=True),
        sa.Column("campaign_name", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=40), nullable=True),
        sa.Column("finish_date", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "dry_run",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("items_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_success", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_promotion_apply_runs_company_code",
        "promotion_apply_runs",
        ["company_code"],
    )
    op.create_index(
        "ix_promotion_apply_runs_company_created",
        "promotion_apply_runs",
        ["company_code", "created_at"],
    )

    op.create_table(
        "promotion_apply_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=100), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("deal_price", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column(
            "response_body",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["promotion_apply_runs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_promotion_apply_items_run",
        "promotion_apply_items",
        ["run_id"],
    )
    op.create_index(
        "ix_promotion_apply_items_item",
        "promotion_apply_items",
        ["item_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_promotion_apply_items_item", table_name="promotion_apply_items")
    op.drop_index("ix_promotion_apply_items_run", table_name="promotion_apply_items")
    op.drop_table("promotion_apply_items")
    op.drop_index(
        "ix_promotion_apply_runs_company_created",
        table_name="promotion_apply_runs",
    )
    op.drop_index(
        "ix_promotion_apply_runs_company_code",
        table_name="promotion_apply_runs",
    )
    op.drop_table("promotion_apply_runs")
