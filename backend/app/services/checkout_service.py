import secrets
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.delivery import calc_delivery_price, calc_lifting_price
from app.enums.availability import AvailabilityEnum
from app.enums.order import (
    AllocationSourceEnum,
    LiftingTypeEnum,
    OrderEventActionEnum,
    OrderServiceTypeEnum,
    OrderStatusEnum,
)
from app.enums.product_status import ProductStatusEnum
from app.models.catalog import Product
from app.models.inventory import SupplierOffer
from app.models.location import Building, ResidentialComplex, ServiceTariff
from app.models.order import Order, OrderAllocation, OrderEvent, OrderLine, OrderServiceLine
from app.repositories.location_repo import LocationRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.pricing_repo import PricingRepository
from app.schemas.checkout import (
    OrderCreatedOut,
    OrderCreateIn,
    OrderLinePublicOut,
    OrderPublicOut,
    QuoteIn,
    QuoteLineOut,
    QuoteOut,
    ServiceOut,
)
from app.schemas.location import BuildingPublicOut

CENT = Decimal("0.01")
ZERO = Decimal("0")

LIFTING_NAMES = {
    LiftingTypeEnum.lift: "Подъём на грузовом лифте",
    LiftingTypeEnum.stairs: "Подъём по лестнице",
}


@dataclass
class _Calculation:
    quote: QuoteOut
    products: dict[int, Product]
    offers: dict[int, SupplierOffer]
    tariff: ServiceTariff | None
    building: Building | None
    complex_: ResidentialComplex | None


def format_address(
    order: Order, building: Building | None = None, complex_: ResidentialComplex | None = None
) -> str:
    """«ЖК Северный, корпус 2, подъезд 1, этаж 7, кв. 45»."""
    parts = (
        [complex_.name, building.name] if building and complex_ else [order.address_text or "Адрес не указан"]
    )
    for label, value in (("подъезд", order.entrance), ("этаж", order.floor), ("кв.", order.apartment)):
        if value:
            parts.append(f"{label} {value}")
    return ", ".join(parts)


class CheckoutService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db=db)
        self.locations = LocationRepository(db=db)
        self.pricing = PricingRepository(db=db)

    # ─── Корпус из QR ─────────────────────────────────────────────────────────

    async def get_building(self, code: str) -> BuildingPublicOut:
        row = await self.locations.get_building_by_code(code=code.lower())
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
        building, complex_ = row
        return BuildingPublicOut(
            code=building.code,
            name=building.name,
            floors=building.floors,
            cargo_lift_length_mm=building.cargo_lift_length_mm,
            complex_name=complex_.name,
            complex_address=complex_.address,
        )

    # ─── Расчёт корзины ───────────────────────────────────────────────────────

    async def quote(self, data: QuoteIn) -> QuoteOut:
        return (await self._calculate(data)).quote

    async def _calculate(self, data: QuoteIn) -> _Calculation:
        # Один товар дважды в корзине считаем одной строкой
        quantities: dict[int, Decimal] = {}
        for item in data.items:
            quantities[item.product_id] = quantities.get(item.product_id, ZERO) + item.quantity

        found = await self.repo.get_products(list(quantities))
        products = {pid: p for pid, p in found.items() if p.status == ProductStatusEnum.published.value}
        removed = [pid for pid in quantities if pid not in products]
        stock = await self.repo.get_stock_available(list(products))
        offers = await self.pricing.get_sellable_offers(list(products.values()))

        building = complex_ = None
        if data.building_code:
            row = await self.locations.get_building_by_code(code=data.building_code.lower())
            if row:
                building, complex_ = row

        lines: list[QuoteLineOut] = []
        weight, weight_unknown = ZERO, False
        for product_id, quantity in quantities.items():
            product = products.get(product_id)
            if product is None:
                continue
            from_stock = stock.get(product_id, ZERO)
            offer = offers.get(product_id)
            available = from_stock + (offer.quantity if offer else ZERO)
            if quantity <= from_stock:
                availability = AvailabilityEnum.in_stock
            elif quantity <= available:
                availability = AvailabilityEnum.on_order
            else:
                availability = AvailabilityEnum.unavailable

            if product.weight_kg is None:
                weight_unknown = True
            else:
                weight += product.weight_kg * quantity
            lift_length = building.cargo_lift_length_mm if building else None
            lines.append(
                QuoteLineOut(
                    product_id=product.id,
                    slug=product.slug,
                    name=product.name,
                    unit=product.unit,
                    image=product.images[0] if product.images else None,
                    quantity=quantity,
                    unit_price=product.price,
                    total=(product.price * quantity).quantize(CENT),
                    availability=availability,
                    available_quantity=available,
                    too_long_for_lift=bool(
                        lift_length and product.length_mm and product.length_mm > lift_length
                    ),
                )
            )

        goods_total = sum((line.total for line in lines), ZERO)
        tariff = await self.locations.get_effective_tariff(complex_id=complex_.id if complex_ else None)
        services: list[ServiceOut] = []
        if tariff is not None and lines:
            services.append(
                ServiceOut(
                    type=OrderServiceTypeEnum.delivery,
                    name="Доставка",
                    price=calc_delivery_price(goods_total, tariff.delivery_price, tariff.delivery_free_from),
                )
            )
            if data.lifting_type != LiftingTypeEnum.none:
                services.append(
                    ServiceOut(
                        type=OrderServiceTypeEnum.lifting,
                        name=LIFTING_NAMES[data.lifting_type],
                        price=calc_lifting_price(
                            lifting_type=data.lifting_type,
                            weight_kg=weight,
                            floor=data.floor,
                            lift_price_per_100kg=tariff.lift_price_per_100kg,
                            lift_min_price=tariff.lift_min_price,
                            stairs_price_per_100kg_floor=tariff.stairs_price_per_100kg_floor,
                        ),
                    )
                )
        services_total = sum((service.price for service in services), ZERO)

        quote = QuoteOut(
            lines=lines,
            removed_product_ids=removed,
            services=services,
            goods_total=goods_total,
            services_total=services_total,
            total=goods_total + services_total,
            total_weight_kg=weight.quantize(Decimal("0.1")),
            weight_unknown=weight_unknown,
            services_unknown=tariff is None,
            can_order=bool(lines)
            and all(line.availability != AvailabilityEnum.unavailable for line in lines),
        )
        return _Calculation(quote, products, offers, tariff, building, complex_)

    # ─── Оформление ───────────────────────────────────────────────────────────

    async def create_order(self, data: OrderCreateIn) -> tuple[OrderCreatedOut, str]:
        """Номер и токен заказа, а также текст уведомления менеджеру."""
        calc = await self._calculate(data)
        quote = calc.quote
        if quote.removed_product_ids:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product unavailable")
        if not quote.can_order:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not enough stock")
        if calc.building is None and not (data.address_text and data.address_text.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Address is required"
            )
        if data.delivery_date and data.delivery_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Delivery date is in the past"
            )

        order = Order(
            public_token=secrets.token_urlsafe(16),
            building_id=calc.building.id if calc.building else None,
            address_text=None if calc.building else data.address_text.strip(),
            entrance=data.entrance,
            floor=str(data.floor) if data.floor else None,
            apartment=data.apartment,
            customer_name=data.customer_name.strip(),
            customer_phone=data.customer_phone,
            contact_channel=data.contact_channel.value,
            missing_item_policy=data.missing_item_policy.value,
            comment=data.comment.strip() if data.comment else None,
            lifting_type=data.lifting_type.value,
            delivery_date=data.delivery_date,
            delivery_slot=data.delivery_slot.value if data.delivery_slot else None,
            source_code=data.source_code,
            goods_total=quote.goods_total,
            services_total=quote.services_total,
            total=quote.total,
        )
        await self.repo.add(order)
        await self.repo.add(
            OrderEvent(
                order_id=order.id,
                action=OrderEventActionEnum.created.value,
                status=OrderStatusEnum.new.value,
            )
        )

        for line in quote.lines:
            order_line = OrderLine(
                order_id=order.id,
                product_id=line.product_id,
                name=line.name,
                unit=line.unit,
                quantity=line.quantity,
                unit_price=line.unit_price,
                total=line.total,
            )
            await self.repo.add(order_line)
            await self._allocate(order_line=order_line, offer=calc.offers.get(line.product_id))

        for service in quote.services:
            await self.repo.add(
                OrderServiceLine(
                    order_id=order.id,
                    type=service.type.value,
                    name=service.name,
                    price=service.price,
                    cost=self._service_cost(service, calc.tariff),
                )
            )

        await self.db.commit()
        created = OrderCreatedOut(number=order.id, public_token=order.public_token)
        return created, self._notification_text(
            order, quote, format_address(order, calc.building, calc.complex_)
        )

    async def _allocate(self, order_line: OrderLine, offer: SupplierOffer | None) -> None:
        """Сначала свой склад с резервом, остаток у партнёра."""
        remaining = order_line.quantity
        # Строки склада заблокированы до commit: два заказа не зарезервируют один мешок
        for stock in await self.repo.get_stock_items_for_update(product_id=order_line.product_id):
            take = min(stock.quantity - stock.reserved, remaining)
            if take <= 0:
                continue
            stock.reserved += take
            remaining -= take
            await self.repo.add(
                OrderAllocation(
                    order_line_id=order_line.id,
                    source_type=AllocationSourceEnum.warehouse.value,
                    warehouse_id=stock.warehouse_id,
                    quantity=take,
                    unit_cost=stock.unit_cost,
                )
            )
            if remaining <= 0:
                return

        if offer is None or offer.quantity < remaining:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not enough stock")
        await self.repo.add(
            OrderAllocation(
                order_line_id=order_line.id,
                source_type=AllocationSourceEnum.supplier.value,
                supplier_offer_id=offer.id,
                quantity=remaining,
                unit_cost=offer.price,
            )
        )

    @staticmethod
    def _service_cost(service: ServiceOut, tariff: ServiceTariff | None) -> Decimal | None:
        if tariff is None:
            return None
        if service.type == OrderServiceTypeEnum.delivery:
            return tariff.delivery_cost
        return (service.price * tariff.lifting_cost_percent / 100).quantize(CENT)

    @staticmethod
    def _notification_text(order: Order, quote: QuoteOut, address: str) -> str:
        # Имя и телефон покупателя в Telegram не отправляем: серверы за рубежом.
        # Менеджер видит их в админке по ссылке
        lines = [
            f"Новый заказ № {order.id} на {quote.total:.0f} ₽",
            address,
        ]
        if order.delivery_date:
            lines.append(f"Доставка: {order.delivery_date:%d.%m}")
        if any(line.availability == AvailabilityEnum.on_order for line in quote.lines):
            lines.append("Есть товары партнёра: подтвердите наличие")
        lines.append(f"{settings.SITE_URL}/manager/orders/{order.id}")
        return "\n".join(lines)

    # ─── Статус для покупателя ────────────────────────────────────────────────

    async def get_public_order(self, token: str) -> OrderPublicOut:
        order = await self.repo.get_order_by_token(token=token)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        buildings = await self.locations.get_buildings_with_complexes(
            [order.building_id] if order.building_id else []
        )
        building, complex_ = buildings.get(order.building_id, (None, None))
        lines = await self.repo.get_lines(order_id=order.id)
        services = await self.repo.get_services(order_id=order.id)
        return OrderPublicOut(
            number=order.id,
            status=order.status,
            created_at=order.created_at,
            address=format_address(order, building, complex_),
            lifting_type=order.lifting_type,
            delivery_date=order.delivery_date,
            delivery_slot=order.delivery_slot,
            lines=[OrderLinePublicOut.model_validate(line, from_attributes=True) for line in lines],
            services=[ServiceOut.model_validate(service, from_attributes=True) for service in services],
            goods_total=order.goods_total,
            services_total=order.services_total,
            total=order.total,
        )
