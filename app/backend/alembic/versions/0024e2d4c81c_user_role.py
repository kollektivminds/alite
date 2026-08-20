"""User role column rename

Revision ID: 0024e2d4c81c
Revises: 993c9078c6cb
Create Date: 2026-08-20
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0024e2d4c81c"
down_revision = "993c9078c6cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------------
    # Rename existing user_role to role without dropping or inserting NULLs
    # ----------------------------------------------------------------------
    op.alter_column(
        "users",
        "user_role",
        new_column_name="role",
        existing_type=sa.String(length=16),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Revert rename
    op.alter_column(
        "users",
        "role",
        new_column_name="user_role",
        existing_type=sa.String(length=32),
        existing_nullable=False,
    )
