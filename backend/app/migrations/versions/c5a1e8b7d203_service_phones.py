"""shop_services.phone and shop_settings with general phone

Revision ID: c5a1e8b7d203
Revises: b3f7c2d9e481
"""

import sqlalchemy as sa
from alembic import op

revision = "c5a1e8b7d203"
down_revision = "b3f7c2d9e481"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("shop_services", sa.Column("phone", sa.String(), nullable=True))
    op.create_table(
        "shop_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO shop_settings (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table("shop_settings")
    op.drop_column("shop_services", "phone")
