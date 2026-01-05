from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import the configured settings object from the central config file
from app.backend.config import settings

# --- Base Engine Configuration ---
def get_engine_url(db_name: str = settings.DB_NAME) -> str:
    """Builds the database URL, optionally overriding the database name."""
    # This uses your existing safe secret access method from config.py
    return f"postgresql://{settings.DB_USER}:{settings.DB_PW.get_secret_value()}@{settings.DB_HOST}:{settings.DB_PORT}/{db_name}"

# --- 1. Default Development Engine ---
# This uses the default DB_NAME for the running application
DATABASE_URL = get_engine_url()
engine = create_engine(DATABASE_URL)

# --- 2. Session Factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 3. API Dependency (Unchanged) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()