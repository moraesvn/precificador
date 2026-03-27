from fastapi import APIRouter

from backend.services.health_service import health_status


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return health_status()
