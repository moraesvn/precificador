from backend.db import Base, engine
from backend.models import (  # noqa: F401
    MLListing,
    MLListingRelation,
    MLListingSku,
    MLSyncRun,
    OAuthConnection,
    OAuthState,
)


def run_startup_tasks() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)
