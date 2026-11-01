from fastapi import APIRouter, Depends, Query

from app.deps.services import get_catalog_service
from app.schemas.catalog import CategoryOut, ProductListOut, ProductOut
from app.services.catalog_service import CatalogService

router = APIRouter(tags=["Platform • Catalog"])


@router.get("/categories/", response_model=list[CategoryOut])
async def list_categories(service: CatalogService = Depends(get_catalog_service)):
    return await service.list_categories()


@router.get("/products/", response_model=ProductListOut)
async def list_products(
    category: str | None = None,
    search: str | None = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: CatalogService = Depends(get_catalog_service),
):
    return await service.list_products(category_slug=category, search=search, skip=skip, limit=limit)


@router.get("/products/{slug}", response_model=ProductOut)
async def get_product(slug: str, service: CatalogService = Depends(get_catalog_service)):
    return await service.get_product(slug=slug)
