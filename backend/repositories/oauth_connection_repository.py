from datetime import datetime

from sqlalchemy.orm import Session

from backend.constants.integrations import CompanyCode, Provider
from backend.models import OAuthConnection


class OAuthConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_company_and_provider(
        self,
        company_code: CompanyCode,
        provider: Provider,
    ) -> OAuthConnection | None:
        return (
            self.db.query(OAuthConnection)
            .filter(
                OAuthConnection.company_code == company_code.upper(),
                OAuthConnection.provider == provider.lower(),
            )
            .first()
        )

    def upsert_connection_tokens(
        self,
        company_code: CompanyCode,
        provider: Provider,
        access_token: str,
        refresh_token: str | None = None,
        token_type: str | None = None,
        scope: str | None = None,
        expires_at: datetime | None = None,
        external_account_id: str | None = None,
    ) -> OAuthConnection:
        record = self.get_by_company_and_provider(company_code, provider)

        if record is None:
            record = OAuthConnection(
                company_code=company_code,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type=token_type,
                scope=scope,
                expires_at=expires_at,
                external_account_id=external_account_id,
                is_active=True,
            )
            self.db.add(record)
        else:
            record.access_token = access_token
            record.refresh_token = refresh_token
            record.token_type = token_type
            record.scope = scope
            record.expires_at = expires_at
            record.external_account_id = external_account_id
            record.is_active = True

        self.db.commit()
        self.db.refresh(record)
        return record
