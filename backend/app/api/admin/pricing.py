from fastapi import APIRouter, Depends, status

from app.deps.auth import require_admin, require_staff
from app.deps.services import get_pricing_service
from app.schemas.pricing import PricingRuleIn, PricingRuleOut, PricingRuleSaveOut
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing-rules", tags=["Admin • Pricing"])


@router.get("/", response_model=list[PricingRuleOut], dependencies=[Depends(require_staff)])
async def list_rules(service: PricingService = Depends(get_pricing_service)):
    return await service.list_rules()


# Наценку меняет только администратор: от неё зависит прибыль
@router.put("/", response_model=PricingRuleSaveOut, dependencies=[Depends(require_admin)])
async def save_rule(data: PricingRuleIn, service: PricingService = Depends(get_pricing_service)):
    return await service.save_rule(data=data)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_rule(rule_id: int, service: PricingService = Depends(get_pricing_service)):
    await service.delete_rule(rule_id=rule_id)
