"""admin catalog: users, pricing rules, supplier feed fields

Revision ID: c3e8a9b41d27
Revises: a1c4f7d20b13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c3e8a9b41d27"
down_revision = "a1c4f7d20b13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("login", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), server_default="manager", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login"),
    )

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("markup_percent", sa.Numeric(6, 2), nullable=False),
        sa.Column("min_profit", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", name="uq_pricing_rules_category"),
    )

    op.add_column(
        "products", sa.Column("is_price_manual", sa.Boolean(), server_default="true", nullable=False)
    )

    op.add_column("suppliers", sa.Column("last_sync_error", sa.String(), nullable=True))
    op.add_column("suppliers", sa.Column("last_sync_summary", postgresql.JSONB(), nullable=True))

    op.add_column("supplier_offers", sa.Column("vendor", sa.String(), nullable=True))
    op.add_column("supplier_offers", sa.Column("category_name", sa.String(), nullable=True))
    op.add_column("supplier_offers", sa.Column("picture_url", sa.String(), nullable=True))
    op.add_column("supplier_offers", sa.Column("weight_kg", sa.Numeric(10, 3), nullable=True))

    # Партнёр и свой склад нужны и на сервере, поэтому заводим их миграцией
    op.execute(
        "INSERT INTO suppliers (code, name, feed_url) "
        "VALUES ('famarket', 'Фамаркет', 'https://famarket.ru/yml/') ON CONFLICT (code) DO NOTHING"
    )
    op.execute(
        "INSERT INTO warehouses (name) SELECT 'Основной склад' WHERE NOT EXISTS (SELECT 1 FROM warehouses)"
    )


def downgrade() -> None:
    op.drop_column("supplier_offers", "weight_kg")
    op.drop_column("supplier_offers", "picture_url")
    op.drop_column("supplier_offers", "category_name")
    op.drop_column("supplier_offers", "vendor")

    op.drop_column("suppliers", "last_sync_summary")
    op.drop_column("suppliers", "last_sync_error")

    op.drop_column("products", "is_price_manual")

    op.drop_table("pricing_rules")
    op.drop_table("users")
