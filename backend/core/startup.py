from backend.db import Base, engine
from backend.models import OAuthConnection, OAuthState  # noqa: F401


def run_startup_tasks() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)
