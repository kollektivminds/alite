"""
ALITE Database Migration Revision
Template: alembic/script.py.mako

Engineering Justification:
- Injects standard typing and SQLModel dependencies automatically into every
  generated migration script.
- Prevents runtime NameErrors during CI/CD pipeline deployments by ensuring
  'sqlmodel' is always in the module namespace when applying schema changes.
"""

from typing import Sequence, Union

import sqlalchemy as sa

# ==============================================================================
# ALITE Custom Framework Imports
# ==============================================================================
import sqlmodel  # Required for SQLModel-specific column types and constraints
from alembic import op

# ==============================================================================
# Alembic Revision Identifiers
# ==============================================================================
revision: str = "02431b21f028"
down_revision: Union[str, None] = "0024e2d4c81c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable the pg_trgm extension
    # Idempotent declaration avoids failing if the DB superuser already activated it
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2. Construct a GIN (Generalized Inverted Index) using trigram operators
    # This turns O(N) sequential scans during func.similarity queries into fast index scans.
    # Replace 'lemmas' with your exact DB table name, and 'lem_text' with your column name.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_lemmas_lem_text_trgm
        ON lemmas
        USING gin (lem_text gin_trgm_ops);
        """)


def downgrade() -> None:
    # 1. Remove the index before removing the extension to avoid dependency conflicts
    op.execute("DROP INDEX IF EXISTS ix_lemmas_lem_text_trgm;")

    # 2. Drop the extension
    # Dropping the extension in production can impact other services if shared,
    # but strictly cleans the schema in sandbox/testing rollbacks.
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
