import os

import psycopg
from fastapi import FastAPI, Query
from sqlalchemy import text

from backend.db import Base, engine
from backend.models import OAuthConnection  # noqa: F401


app = FastAPI(title="Precificador OAuth API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    database_url = os.getenv("DATABASE_URL")
    database_url_configured = bool(database_url)
    database_connected = False
    oauth_table_ready = False

    if database_url_configured:
        try:
            psycopg_dsn = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
            with psycopg.connect(psycopg_dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            database_connected = True
        except Exception:
            database_connected = False

    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM oauth_connections LIMIT 1"))
            oauth_table_ready = True
        except Exception:
            oauth_table_ready = False

    return {
        "status": "ok",
        "database_url_configured": str(database_url_configured).lower(),
        "database_connected": str(database_connected).lower(),
        "oauth_table_ready": str(oauth_table_ready).lower(),
    }


@app.get("/oauth/tiny/callback")
def tiny_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> dict[str, str | None]:
    return {
        "provider": "tiny",
        "message": "Callback recebido com sucesso.",
        "code": code,
        "state": state,
        "error": error,
    }


@app.get("/oauth/ml/callback/")
@app.get("/oauth/ml/callback")
def ml_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> dict[str, str | None]:
    return {
        "provider": "ml",
        "message": "Callback recebido com sucesso.",
        "code": code,
        "state": state,
        "error": error,
    }
