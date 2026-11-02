"""staff cabinets: courier assignment, planned delivery, cash and order history

Revision ID: e7a3c9d15f62
Revises: d5f1b2c63e48
"""

import sqlalchemy as sa
from alembic import op

revision = "e7a3c9d15f62"
down_revision = "d5f1b2c63e48"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("courier_id", sa.BigInteger(), nullable=True))
    op.add_column("orders", sa.Column("planned_date", sa.Date(), nullable=True))
    op.add_column("orders", sa.Column("planned_slot", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("cash_received", sa.Numeric(12, 2), nullable=True))
    op.add_column("orders", sa.Column("delivered_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_foreign_key(
        "orders_courier_id_fkey", "orders", "users", ["courier_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_orders_courier_id", "orders", ["courier_id"])
    op.create_index("ix_orders_planned_date", "orders", ["planned_date"])

    op.create_table(
        "order_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_events_order_id", "order_events", ["order_id"])
    op.create_index("ix_order_events_user_id", "order_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_order_events_user_id", table_name="order_events")
    op.drop_index("ix_order_events_order_id", table_name="order_events")
    op.drop_table("order_events")

    op.drop_index("ix_orders_planned_date", table_name="orders")
    op.drop_index("ix_orders_courier_id", table_name="orders")
    op.drop_constraint("orders_courier_id_fkey", "orders", type_="foreignkey")
    op.drop_column("orders", "delivered_at")
    op.drop_column("orders", "cash_received")
    op.drop_column("orders", "planned_slot")
    op.drop_column("orders", "planned_date")
    op.drop_column("orders", "courier_id")
