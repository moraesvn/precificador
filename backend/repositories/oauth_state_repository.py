from datetime import datetime

from sqlalchemy.orm import Session

from backend.constants.integrations import CompanyCode, Provider
from backend.models import OAuthState


class OAuthStateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_state(
        self,
        state: str,
        company_code: CompanyCode,
        provider: Provider,
        code_verifier: str,
        expires_at: datetime,
    ) -> OAuthState:
        record = OAuthState(
            state=state,
            company_code=company_code,
            provider=provider,
            code_verifier=code_verifier,
            expires_at=expires_at,
            used_at=None,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_state(self, state: str) -> OAuthState | None:
        return self.db.query(OAuthState).filter(OAuthState.state == state).first()

    def mark_as_used(self, oauth_state: OAuthState, used_at: datetime) -> OAuthState:
        oauth_state.used_at = used_at
        self.db.commit()
        self.db.refresh(oauth_state)
        return oauth_state
