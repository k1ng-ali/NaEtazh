from fastapi import APIRouter, Depends, status

from app.deps.auth import require_admin
from app.deps.services import get_pricing_service
from app.schemas.pricing import ProductPriceIn, ProductPriceOut
from app.services.pricing_service import PricingService

# Точная цена определяет прибыль, как и наценка, поэтому раздел только для владельца
router = APIRouter(prefix="/product-prices", tags=["Admin • Pricing"], dependencies=[Depends(require_admin)])


@router.get("/", response_model=list[ProductPriceOut])
async def list_product_prices(service: PricingService = Depends(get_pricing_service)):
    return await service.list_product_prices()


@router.put("/", response_model=ProductPriceOut)
async def save_product_price(data: ProductPriceIn, service: PricingService = Depends(get_pricing_service)):
    return await service.save_product_price(data=data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_price(product_id: int, service: PricingService = Depends(get_pricing_service)):
    await service.delete_product_price(product_id=product_id)
