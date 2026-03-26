import os

from fastapi import FastAPI, Query


app = FastAPI(title="Precificador OAuth API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    database_url = os.getenv("DATABASE_URL")
    return {"status": "ok", "database_url_configured": str(bool(database_url)).lower()}


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
