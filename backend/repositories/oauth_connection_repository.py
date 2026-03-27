from sqlalchemy.orm import Session

from backend.models import OAuthConnection


class OAuthConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_company_and_provider(self, company_code: str, provider: str) -> OAuthConnection | None:
        return (
            self.db.query(OAuthConnection)
            .filter(
                OAuthConnection.company_code == company_code.upper(),
                OAuthConnection.provider == provider,
            )
            .first()
        )
