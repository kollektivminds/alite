"""alembic/env.py
ALITE Database Migration Environment Configuration
"""

import logging
from logging.config import fileConfig

import alite_backend.db.models
from alembic import context
from alite_backend.config import settings
from sqlalchemy import engine_from_config, pool, text
from sqlmodel import SQLModel

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
    """Run migrations in 'online' mode with lock timeout safeguards."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DEV_DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # NullPool ensures migration does not leak idle connections
    )

    with connectable.connect() as connection:
        # Prevent indefinite hang: abort if lock cannot be acquired within 10 seconds
        connection.execute(text("SET lock_timeout = '10s';"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,
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
