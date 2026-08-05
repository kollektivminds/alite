"""alembic/env.py
ALITE Database Migration Environment Configuration
"""

import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

import alite_backend.db.models
from alite_backend.config import settings

# alembic config
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# the SQLModel metadata registry
target_metadata = SQLModel.metadata

# inject the dynamic database URL from Pydantic into Alembic's configuration
config.set_main_option("sqlalchemy.url", settings.DEV_DATABASE_URL)


def run_migrations_online() -> None:
    """Executes migrations in 'online' mode against the PostgreSQL container."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
