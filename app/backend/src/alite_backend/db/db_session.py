from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alite_backend.config import settings

# --- 1. Default Development Engine ---
engine = create_engine(settings.DATABASE_URL)

# --- 2. Session Factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 3. API Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()