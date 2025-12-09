from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import the configured settings object from the central config file
from app.backend.config import settings

# --- 1. Define the Database URL using the central config object ---
# The settings object already securely computes the full URL using pydantic.SecretStr
DATABASE_URL = settings.DATABASE_URL

# --- 2. Create the SQLAlchemy Engine ---
# The engine is the starting point for any SQLAlchemy application.
# It establishes the connection pool to the database.
engine = create_engine(DATABASE_URL)

# --- 3. Create a Session Factory ---
# This is a factory that will generate new Session objects (database connections).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 4. Create a Dependency for your API (FastAPI) ---
# This is the function you'll use for Dependency Injection in your API endpoints.
# It ensures the database connection is managed (opened on request, closed on finish).
def get_db():
    db = SessionLocal()
    try:
        # Provide the database session
        yield db
    finally:
        # Close the connection when the request is finished
        db.close()