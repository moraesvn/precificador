from fastapi import FastAPI

from backend.api.routes.health import router as health_router
from backend.api.routes.oauth_ml import router as oauth_ml_router
from backend.api.routes.oauth_tiny import router as oauth_tiny_router
from backend.core.startup import run_startup_tasks


app = FastAPI(title="Precificador OAuth API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    run_startup_tasks()


app.include_router(health_router)
app.include_router(oauth_tiny_router)
app.include_router(oauth_ml_router)
