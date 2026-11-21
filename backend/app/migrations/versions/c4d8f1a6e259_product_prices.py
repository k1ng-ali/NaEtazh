"""product_prices: exact sale price per product with a profit floor

Revision ID: c4d8f1a6e259
Revises: b9c2e5f7a314
"""

import sqlalchemy as sa
from alembic import op

revision = "c4d8f1a6e259"
down_revision = "b9c2e5f7a314"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_prices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("min_profit", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )


def downgrade() -> None:
    op.drop_table("product_prices")
