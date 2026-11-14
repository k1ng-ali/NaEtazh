from decimal import Decimal
from itertools import count
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.models import Category, Product
from app.repositories.pricing_repo import PricingRepository
from app.services.catalog_service import CatalogService
from app.services.partner_catalog_service import CategoryResolver, PartnerCatalogService, unique_value


def make_db():
    """Сессия без базы: flush раздаёт id всему, что добавили."""
    db = AsyncMock()
    added = []
    ids = count(100)
    db.add = MagicMock(side_effect=added.append)
    db.add_all = MagicMock(side_effect=added.extend)

    async def flush():
        for item in added:
            if getattr(item, "id", None) is None:
                item.id = next(ids)

    db.flush = AsyncMock(side_effect=flush)
    return db, added


def supplier_category(external_id, name, parent=None, category_id=None):
    return SimpleNamespace(
        external_id=external_id, name=name, parent_external_id=parent, category_id=category_id
    )


TREE = [
    supplier_category("1", "Смеси строительные"),
    supplier_category("2", "Шпаклевка", parent="1"),
    supplier_category("3", "Сухая шпаклевка в мешках", parent="2"),
    supplier_category("9", "АКЦИЯ!"),
]


async def test_resolver_builds_two_levels_and_folds_deeper_ones():
    db, added = make_db()
    resolver = CategoryResolver(db=db, rows=TREE, slugs={"shpaklevka"}, position=10)

    deep = await resolver.resolve("3")
    second = await resolver.resolve("2")

    categories = [item for item in added if isinstance(item, Category)]
    assert [(c.name, c.slug, c.position) for c in categories] == [
        ("Смеси строительные", "smesi-stroitelnye", 11),
        ("Шпаклевка", "shpaklevka-2", 12),
    ]
    root, child = categories
    assert child.parent_id == root.id
    assert deep == second == child.id
    # Глубокая категория своего раздела не получает, наследует подраздел
    assert TREE[2].category_id is None


async def test_resolver_respects_manual_mapping_and_hides_service_categories():
    db, added = make_db()
    rows = [supplier_category("1", "Смеси"), supplier_category("2", "Шпаклевка", parent="1", category_id=7)]
    resolver = CategoryResolver(
        db=db, rows=rows + [supplier_category("9", "АКЦИЯ!")], slugs=set(), position=0
    )

    assert await resolver.resolve("2") == 7
    assert await resolver.resolve("unknown") is None
    await resolver.resolve("9")

    assert [c.is_active for c in added] == [False]


def test_unique_value_adds_suffix():
    taken = {"a", "a-2"}

    assert unique_value("a", taken) == "a-3"
    assert unique_value("b", taken) == "b"
    assert {"a-3", "b"} <= taken


async def test_create_products_publishes_offers_with_auto_price():
    db, added = make_db()
    service = PartnerCatalogService(db=db)
    offers = [
        SimpleNamespace(
            external_id="00-1",
            name="Шпаклевка Ветонит LR+, 20 кг",
            price=Decimal("640.00"),
            weight_kg=Decimal("20"),
            vendor="Weber",
            category_external_id="3",
            product_id=None,
        ),
        SimpleNamespace(
            external_id="00-2",
            name="Без раздела",
            price=Decimal("10"),
            weight_kg=None,
            vendor=None,
            category_external_id=None,
            product_id=None,
        ),
    ]
    service.repo.get_offers_without_product = AsyncMock(return_value=offers)
    service.repo.get_supplier_categories = AsyncMock(return_value=[supplier_category("3", "Шпаклевка")])
    service.repo.get_category_slugs = AsyncMock(return_value=set())
    service.repo.get_next_category_position = AsyncMock(return_value=0)
    service.repo.get_product_slugs_and_skus = AsyncMock(
        return_value=({"shpaklevka-vetonit-lr-20-kg"}, {"FA-00-1"})
    )

    created = await service.create_products(supplier=SimpleNamespace(id=1, code="famarket"))

    assert created == 1
    product = next(item for item in added if isinstance(item, Product))
    assert product.sku == "FA-00-1-2"
    assert product.slug == "shpaklevka-vetonit-lr-20-kg-2"
    assert product.status == "published"
    assert product.is_price_manual is False
    assert product.images == []
    assert product.attributes == {"Бренд": "Weber"}
    assert offers[0].product_id == product.id
    assert offers[1].product_id is None


async def test_sellable_offers_need_storefront_supplier_and_markup():
    repo = PricingRepository(db=AsyncMock())
    offer = SimpleNamespace(quantity=Decimal("5"))
    repo.get_best_offers = AsyncMock(return_value={1: offer, 2: offer, 3: offer})
    repo.get_rules = AsyncMock(return_value=[SimpleNamespace(category_id=20)])
    products = [
        SimpleNamespace(id=1, category_id=10, is_price_manual=True),
        SimpleNamespace(id=2, category_id=20, is_price_manual=False),
        SimpleNamespace(id=3, category_id=30, is_price_manual=False),
    ]

    offers = await repo.get_sellable_offers(products)

    repo.get_best_offers.assert_awaited_once_with([1, 2, 3], storefront_only=True)
    assert set(offers) == {1, 2}


async def test_list_categories_shows_parents_of_visible_and_hides_under_inactive():
    service = CatalogService(db=AsyncMock())
    categories = [
        SimpleNamespace(id=1, parent_id=None, name="Смеси", slug="smesi", position=1),
        SimpleNamespace(id=2, parent_id=1, name="Шпаклевка", slug="shpaklevka", position=2),
        SimpleNamespace(id=3, parent_id=None, name="Пустой", slug="empty", position=3),
        # Родитель 4 выключен и в список активных не попал
        SimpleNamespace(id=5, parent_id=4, name="Под выключенным", slug="hidden", position=5),
    ]
    service.repo.get_active_categories = AsyncMock(return_value=categories)
    service.repo.get_visible_category_ids = AsyncMock(return_value={2, 5})

    result = await service.list_categories()

    assert [item.slug for item in result] == ["smesi", "shpaklevka"]
