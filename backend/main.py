from fastapi import FastAPI

from backend.api.routes.health import router as health_router
from backend.api.routes.ml_conta import router as ml_conta_router
from backend.api.routes.ml_precos import router as ml_precos_router
from backend.api.routes.ml_sync import router as ml_sync_router
from backend.api.routes.oauth_ml import router as oauth_ml_router
from backend.api.routes.oauth_tiny import router as oauth_tiny_router
from backend.api.routes.promotions_apply import router as promotions_apply_router
from backend.api.routes.promotions_preview import router as promotions_preview_router
from backend.api.routes.promotions_settings import router as promotions_settings_router
from backend.api.routes.tiny_ordens_compra import router as tiny_ordens_compra_router
from backend.api.routes.tiny_produtos import router as tiny_produtos_router
from backend.core.startup import run_startup_tasks


app = FastAPI(title="Precificador OAuth API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    run_startup_tasks()


app.include_router(health_router)
app.include_router(oauth_tiny_router)
app.include_router(tiny_produtos_router)
app.include_router(tiny_ordens_compra_router)
app.include_router(oauth_ml_router)
app.include_router(ml_conta_router)
app.include_router(ml_precos_router)
app.include_router(ml_sync_router)
app.include_router(promotions_settings_router)
app.include_router(promotions_preview_router)
app.include_router(promotions_apply_router)
