from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_staff
from app.deps.services import get_supplier_service
from app.schemas.supplier import (
    OfferCreateProductIn,
    OfferCreateProductOut,
    OfferLinkIn,
    OfferListOut,
    OfferMatchFilterEnum,
    OfferOut,
    SupplierOut,
    SupplierSyncOut,
)
from app.services.supplier_service import SupplierService

router = APIRouter(tags=["Manager • Suppliers"], dependencies=[Depends(require_staff)])


@router.get("/suppliers/", response_model=list[SupplierOut])
async def list_suppliers(service: SupplierService = Depends(get_supplier_service)):
    return await service.list_suppliers()


@router.post("/suppliers/{supplier_id}/sync", response_model=SupplierSyncOut)
async def sync_supplier(supplier_id: int, service: SupplierService = Depends(get_supplier_service)):
    return await service.sync_supplier(supplier_id=supplier_id)


@router.get("/offers/", response_model=OfferListOut)
async def list_offers(
    supplier_id: int | None = None,
    match: OfferMatchFilterEnum = OfferMatchFilterEnum.all,
    search: str | None = Query(None, max_length=100),
    in_stock: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: SupplierService = Depends(get_supplier_service),
):
    return await service.list_offers(
        supplier_id=supplier_id,
        match=match.value,
        search=search,
        in_stock=in_stock,
        skip=skip,
        limit=limit,
    )


@router.post("/offers/{offer_id}/link", response_model=OfferOut)
async def link_offer(
    offer_id: int, data: OfferLinkIn, service: SupplierService = Depends(get_supplier_service)
):
    return await service.link_offer(offer_id=offer_id, product_id=data.product_id)


@router.post("/offers/{offer_id}/unlink", response_model=OfferOut)
async def unlink_offer(offer_id: int, service: SupplierService = Depends(get_supplier_service)):
    return await service.unlink_offer(offer_id=offer_id)


@router.post("/offers/{offer_id}/create-product", response_model=OfferCreateProductOut)
async def create_product_from_offer(
    offer_id: int,
    data: OfferCreateProductIn,
    service: SupplierService = Depends(get_supplier_service),
):
    return await service.create_product_from_offer(offer_id=offer_id, category_id=data.category_id)
