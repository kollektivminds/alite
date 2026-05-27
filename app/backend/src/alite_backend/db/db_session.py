from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alite_backend.config import settings

ENV_MODE = settings.ENV_MODE
if ENV_MODE == "prod":
    DATABASE_URL = str(settings.PROD_DATABASE_URL)
elif ENV_MODE == "test":
    DATABASE_URL = str(settings.TEST_DATABASE_URL)
else:
    DATABASE_URL = str(settings.DEV_DATABASE_URL)

# --- 1. Default Development Engine ---
engine = create_engine(DATABASE_URL)

# --- 2. Session Factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- 3. API Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
