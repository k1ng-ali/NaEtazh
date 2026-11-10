"""users: session_version to end old sessions after password change

Revision ID: f2b6d8e41a93
Revises: e7a3c9d15f62
"""

import sqlalchemy as sa
from alembic import op

revision = "f2b6d8e41a93"
down_revision = "e7a3c9d15f62"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("session_version", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "session_version")
