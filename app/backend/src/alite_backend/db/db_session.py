# backend/src/alite_backend/sb/db_session.py

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from alite_backend.config import settings

logger = logging.getLogger(__name__)

ENV_MODE = settings.ENV_MODE
if ENV_MODE == "prod":
    DATABASE_URL = str(settings.PROD_DATABASE_URL)
elif ENV_MODE == "test":
    DATABASE_URL = str(settings.TEST_DATABASE_URL)
else:
    DATABASE_URL = str(settings.DEV_DATABASE_URL)

# --- 1. Default Development Engine ---
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
)

# --- 2. Session Factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- 3. API Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
