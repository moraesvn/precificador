from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
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
