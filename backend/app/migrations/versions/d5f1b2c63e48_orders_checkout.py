"""orders checkout: service tariffs, delivery wishes and lifting type

Revision ID: d5f1b2c63e48
Revises: c3e8a9b41d27
"""

import sqlalchemy as sa
from alembic import op

revision = "d5f1b2c63e48"
down_revision = "c3e8a9b41d27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_tariffs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("complex_id", sa.BigInteger(), nullable=True),
        sa.Column("delivery_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivery_free_from", sa.Numeric(12, 2), nullable=True),
        sa.Column("delivery_cost", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("lift_price_per_100kg", sa.Numeric(12, 2), nullable=False),
        sa.Column("lift_min_price", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("stairs_price_per_100kg_floor", sa.Numeric(12, 2), nullable=False),
        sa.Column("lifting_cost_percent", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["complex_id"], ["residential_complexes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complex_id", name="uq_service_tariffs_complex"),
    )

    op.add_column("orders", sa.Column("lifting_type", sa.String(), server_default="none", nullable=False))
    op.add_column("orders", sa.Column("delivery_date", sa.Date(), nullable=True))
    op.add_column("orders", sa.Column("delivery_slot", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "delivery_slot")
    op.drop_column("orders", "delivery_date")
    op.drop_column("orders", "lifting_type")

    op.drop_table("service_tariffs")
