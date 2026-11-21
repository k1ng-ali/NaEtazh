"""products: search_text and search_vector for storefront search

Revision ID: b9c2e5f7a314
Revises: e9b3c6d1f478
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import TSVECTOR

revision = "b9c2e5f7a314"
down_revision = "e9b3c6d1f478"
branch_labels = None
depends_on = None

# Копия PRODUCT_SEARCH_TEXT_SQL на момент миграции: модель может поменяться, миграция нет
SEARCH_TEXT_SQL = "translate(lower(name || ' ' || coalesce(attributes ->> 'Бренд', '')), 'ёx', 'ех')"


def upgrade() -> None:
    # Триграммы: поиск по части слова и с опечатками
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.add_column(
        "products",
        sa.Column("search_text", sa.Text(), sa.Computed(SEARCH_TEXT_SQL, persisted=True), nullable=False),
    )
    op.add_column(
        "products",
        sa.Column(
            "search_vector",
            TSVECTOR(),
            sa.Computed(f"to_tsvector('russian'::regconfig, {SEARCH_TEXT_SQL})", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_products_search_text_trgm",
        "products",
        ["search_text"],
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )
    op.create_index("ix_products_search_vector", "products", ["search_vector"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_products_search_vector", table_name="products")
    op.drop_index("ix_products_search_text_trgm", table_name="products")
    op.drop_column("products", "search_vector")
    op.drop_column("products", "search_text")
    # Расширение не удаляем: им могут пользоваться и другие таблицы
