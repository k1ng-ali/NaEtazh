"""suppliers: storefront toggle, partner category tree

Revision ID: a8d4e6f2c915
Revises: f2b6d8e41a93
"""

import sqlalchemy as sa
from alembic import op

revision = "a8d4e6f2c915"
down_revision = "f2b6d8e41a93"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "suppliers", sa.Column("show_on_storefront", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column("supplier_offers", sa.Column("category_external_id", sa.String(), nullable=True))
    op.create_table(
        "supplier_categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("supplier_id", sa.BigInteger(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("parent_external_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", "external_id", name="uq_supplier_categories_supplier_external"),
    )
    op.create_index("ix_supplier_categories_supplier_id", "supplier_categories", ["supplier_id"])


def downgrade() -> None:
    op.drop_index("ix_supplier_categories_supplier_id", table_name="supplier_categories")
    op.drop_table("supplier_categories")
    op.drop_column("supplier_offers", "category_external_id")
    op.drop_column("suppliers", "show_on_storefront")
