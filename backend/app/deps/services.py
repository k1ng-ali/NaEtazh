from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.admin_catalog_service import AdminCatalogService
from app.services.admin_order_service import AdminOrderService
from app.services.auth_service import AuthService
from app.services.catalog_service import CatalogService
from app.services.checkout_service import CheckoutService
from app.services.courier_service import CourierService
from app.services.dashboard_service import DashboardService
from app.services.location_service import LocationService
from app.services.pricing_service import PricingService
from app.services.service_catalog_service import ServiceCatalogService
from app.services.supplier_service import SupplierService
from app.services.user_service import UserService


async def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(db=db)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


async def get_admin_catalog_service(db: AsyncSession = Depends(get_db)) -> AdminCatalogService:
    return AdminCatalogService(db=db)


async def get_supplier_service(db: AsyncSession = Depends(get_db)) -> SupplierService:
    return SupplierService(db=db)


async def get_pricing_service(db: AsyncSession = Depends(get_db)) -> PricingService:
    return PricingService(db=db)


async def get_checkout_service(db: AsyncSession = Depends(get_db)) -> CheckoutService:
    return CheckoutService(db=db)


async def get_admin_order_service(db: AsyncSession = Depends(get_db)) -> AdminOrderService:
    return AdminOrderService(db=db)


async def get_location_service(db: AsyncSession = Depends(get_db)) -> LocationService:
    return LocationService(db=db)


async def get_courier_service(db: AsyncSession = Depends(get_db)) -> CourierService:
    return CourierService(db=db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db=db)


async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db=db)


async def get_service_catalog_service(db: AsyncSession = Depends(get_db)) -> ServiceCatalogService:
    return ServiceCatalogService(db=db)
