"""Configs de promoção (marketplace + tipos)

Revision ID: 20260730_01
Revises: 20260729_02
Create Date: 2026-07-30 15:50:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260730_01"
down_revision: str | None = "20260729_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marketplace_promotion_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("marketplace", sa.String(length=30), nullable=False),
        sa.Column(
            "price_base_source",
            sa.String(length=20),
            server_default="tiny",
            nullable=False,
        ),
        sa.Column(
            "global_adjust_kind",
            sa.String(length=20),
            server_default="percent",
            nullable=False,
        ),
        sa.Column(
            "global_adjust_value",
            sa.Numeric(precision=14, scale=4),
            server_default="0",
            nullable=False,
        ),
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
            "marketplace",
            name="uq_marketplace_promotion_settings",
        ),
    )
    op.create_index(
        "ix_marketplace_promotion_settings_company_code",
        "marketplace_promotion_settings",
        ["company_code"],
    )
    op.create_index(
        "ix_marketplace_promotion_settings_marketplace",
        "marketplace_promotion_settings",
        ["marketplace"],
    )

    op.create_table(
        "promotion_type_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_code", sa.String(length=10), nullable=False),
        sa.Column("marketplace", sa.String(length=30), nullable=False),
        sa.Column("promotion_type", sa.String(length=50), nullable=False),
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("discount_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            "marketplace",
            "promotion_type",
            name="uq_promotion_type_settings",
        ),
    )
    op.create_index(
        "ix_promotion_type_settings_company_mkt",
        "promotion_type_settings",
        ["company_code", "marketplace"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_promotion_type_settings_company_mkt",
        table_name="promotion_type_settings",
    )
    op.drop_table("promotion_type_settings")
    op.drop_index(
        "ix_marketplace_promotion_settings_marketplace",
        table_name="marketplace_promotion_settings",
    )
    op.drop_index(
        "ix_marketplace_promotion_settings_company_code",
        table_name="marketplace_promotion_settings",
    )
    op.drop_table("marketplace_promotion_settings")
