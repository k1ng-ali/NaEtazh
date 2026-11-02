from fastapi import APIRouter

# ─── Admin ────────────────────────────────────────────────────────────────────
from app.api.admin.catalog import router as admin_catalog_router
from app.api.admin.pricing import router as admin_pricing_router
from app.api.admin.suppliers import router as admin_suppliers_router

# ─── Общие ────────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router

# ─── Platform ─────────────────────────────────────────────────────────────────
from app.api.platform.catalog import router as platform_catalog_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(platform_catalog_router)

api_router.include_router(admin_catalog_router, prefix="/admin")
api_router.include_router(admin_suppliers_router, prefix="/admin")
api_router.include_router(admin_pricing_router, prefix="/admin")
