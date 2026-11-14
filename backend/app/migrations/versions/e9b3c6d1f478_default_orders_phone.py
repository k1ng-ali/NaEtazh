"""shop_settings: phone for orders from the client

Revision ID: e9b3c6d1f478
Revises: d7e2f4a9b136
"""

from alembic import op

revision = "e9b3c6d1f478"
down_revision = "d7e2f4a9b136"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Телефон по заказам, который дал клиент. Владелец меняет его в разделе «Услуги»,
    # уже заданный номер не трогаем
    op.execute("UPDATE shop_settings SET phone = '+7 (962) 925-87-87' WHERE id = 1 AND phone IS NULL")


def downgrade() -> None:
    pass
