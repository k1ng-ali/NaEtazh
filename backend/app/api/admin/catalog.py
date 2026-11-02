from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.media import MAX_UPLOAD_BYTES
from app.deps.auth import require_staff
from app.deps.services import get_admin_catalog_service
from app.enums.product_status import ProductStatusEnum
from app.schemas.admin_catalog import (
    CategoryIn,
    CategoryOutAdmin,
    CategoryUpdate,
    ProductIn,
    ProductListOutAdmin,
    ProductOutAdmin,
    ProductUpdate,
    StockIn,
    WarehouseOut,
)
from app.services.admin_catalog_service import AdminCatalogService

router = APIRouter(tags=["Admin • Catalog"], dependencies=[Depends(require_staff)])


# ─── Категории ────────────────────────────────────────────────────────────────


@router.get("/categories/", response_model=list[CategoryOutAdmin])
async def list_categories(service: AdminCatalogService = Depends(get_admin_catalog_service)):
    return await service.list_categories()


@router.post("/categories/", response_model=CategoryOutAdmin, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryIn, service: AdminCatalogService = Depends(get_admin_catalog_service)
):
    return await service.create_category(data=data)


@router.patch("/categories/{category_id}", response_model=CategoryOutAdmin)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    service: AdminCatalogService = Depends(get_admin_catalog_service),
):
    return await service.update_category(category_id=category_id, data=data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int, service: AdminCatalogService = Depends(get_admin_catalog_service)
):
    await service.delete_category(category_id=category_id)


# ─── Товары ───────────────────────────────────────────────────────────────────


@router.get("/products/", response_model=ProductListOutAdmin)
async def list_products(
    search: str | None = Query(None, max_length=100),
    category_id: int | None = None,
    status: ProductStatusEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: AdminCatalogService = Depends(get_admin_catalog_service),
):
    return await service.list_products(
        search=search,
        category_id=category_id,
        status=status.value if status else None,
        skip=skip,
        limit=limit,
    )


@router.post("/products/", response_model=ProductOutAdmin, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductIn, service: AdminCatalogService = Depends(get_admin_catalog_service)):
    return await service.create_product(data=data)


@router.get("/products/{product_id}", response_model=ProductOutAdmin)
async def get_product(product_id: int, service: AdminCatalogService = Depends(get_admin_catalog_service)):
    return await service.get_product(product_id=product_id)


@router.patch("/products/{product_id}", response_model=ProductOutAdmin)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    service: AdminCatalogService = Depends(get_admin_catalog_service),
):
    return await service.update_product(product_id=product_id, data=data)


@router.post("/products/{product_id}/images", response_model=ProductOutAdmin)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    service: AdminCatalogService = Depends(get_admin_catalog_service),
):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Image is larger than 10 MB"
        )
    return await service.add_product_image(product_id=product_id, content=content)


@router.put("/products/{product_id}/stock", response_model=ProductOutAdmin)
async def set_product_stock(
    product_id: int,
    data: StockIn,
    service: AdminCatalogService = Depends(get_admin_catalog_service),
):
    return await service.set_stock(product_id=product_id, data=data)


# ─── Склады ───────────────────────────────────────────────────────────────────


@router.get("/warehouses/", response_model=list[WarehouseOut])
async def list_warehouses(service: AdminCatalogService = Depends(get_admin_catalog_service)):
    return await service.list_warehouses()
