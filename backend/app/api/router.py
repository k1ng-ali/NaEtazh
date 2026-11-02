from fastapi import APIRouter

# ─── Admin: владелец ──────────────────────────────────────────────────────────
from app.api.admin.dashboard import router as admin_dashboard_router
from app.api.admin.locations import router as admin_locations_router
from app.api.admin.orders import router as admin_orders_router
from app.api.admin.pricing import router as admin_pricing_router
from app.api.admin.users import router as admin_users_router

# ─── Общие ────────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router

# ─── Courier: доставка ────────────────────────────────────────────────────────
from app.api.courier.orders import router as courier_orders_router

# ─── Manager: заказы и каталог ────────────────────────────────────────────────
from app.api.manager.catalog import router as manager_catalog_router
from app.api.manager.orders import router as manager_orders_router
from app.api.manager.suppliers import router as manager_suppliers_router

# ─── Platform: покупатели ─────────────────────────────────────────────────────
from app.api.platform.catalog import router as platform_catalog_router
from app.api.platform.checkout import router as platform_checkout_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(platform_catalog_router)
api_router.include_router(platform_checkout_router)

api_router.include_router(manager_orders_router, prefix="/manager")
api_router.include_router(manager_catalog_router, prefix="/manager")
api_router.include_router(manager_suppliers_router, prefix="/manager")

api_router.include_router(courier_orders_router, prefix="/courier")

api_router.include_router(admin_dashboard_router, prefix="/admin")
api_router.include_router(admin_orders_router, prefix="/admin")
api_router.include_router(admin_users_router, prefix="/admin")
api_router.include_router(admin_pricing_router, prefix="/admin")
api_router.include_router(admin_locations_router, prefix="/admin")
