"""categories: image for home tiles

Revision ID: d7e2f4a9b136
Revises: c5a1e8b7d203
"""

import sqlalchemy as sa
from alembic import op

revision = "d7e2f4a9b136"
down_revision = "c5a1e8b7d203"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("image", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("categories", "image")
