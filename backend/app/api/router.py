from fastapi import APIRouter

# ─── Platform ─────────────────────────────────────────────────────────────────
from app.api.platform.catalog import router as platform_catalog_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(platform_catalog_router)
