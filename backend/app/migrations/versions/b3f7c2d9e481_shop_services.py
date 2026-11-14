"""shop_services and service_requests

Revision ID: b3f7c2d9e481
Revises: a8d4e6f2c915
"""

import sqlalchemy as sa
from alembic import op

revision = "b3f7c2d9e481"
down_revision = "a8d4e6f2c915"
branch_labels = None
depends_on = None

# Стартовый список, тексты и цены владелец меняет в админке
SERVICES = [
    (
        "dostavka-gruzov",
        "Доставка грузов",
        "Привезём стройматериалы и поднимем в квартиру",
        "Перевезём стройматериалы и другие грузы по городу: из магазина, со склада или от вас. "
        "Грузчики поднимут на этаж на лифте или по лестнице.",
    ),
    (
        "vynos-musora",
        "Вынос мусора",
        "Строительный мусор в мешках и крупногабарит",
        "Вынесем строительный мусор после ремонта, погрузим и вывезем на полигон. "
        "Мешки можем привезти заранее.",
    ),
    (
        "demontazh",
        "Демонтаж",
        "Стены, перегородки, плитка, полы",
        "Демонтируем перегородки, плитку, стяжку, старые полы и сантехнику. " "Мусор можно сразу вывезти.",
    ),
    (
        "nalivnye-styazhki",
        "Наливные стяжки",
        "Ровный пол под ламинат, плитку и линолеум",
        "Зальём стяжку и наливной пол: замерим перепады, подберём смесь, привезём материалы.",
    ),
]


def upgrade() -> None:
    op.create_table(
        "shop_services",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_text", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "service_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("service_id", sa.BigInteger(), nullable=True),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="new", nullable=False),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("customer_phone", sa.String(), nullable=False),
        sa.Column("building_id", sa.BigInteger(), nullable=True),
        sa.Column("address_text", sa.String(), nullable=True),
        sa.Column("apartment", sa.String(), nullable=True),
        sa.Column("preferred_date", sa.Date(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("source_code", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["shop_services.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_requests_status", "service_requests", ["status"])
    op.create_index("ix_service_requests_created_at", "service_requests", ["created_at"])

    table = sa.table(
        "shop_services",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("summary", sa.String),
        sa.column("description", sa.Text),
        sa.column("position", sa.Integer),
    )
    op.bulk_insert(
        table,
        [
            {"slug": slug, "name": name, "summary": summary, "description": description, "position": index}
            for index, (slug, name, summary, description) in enumerate(SERVICES, start=1)
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_service_requests_created_at", table_name="service_requests")
    op.drop_index("ix_service_requests_status", table_name="service_requests")
    op.drop_table("service_requests")
    op.drop_table("shop_services")
