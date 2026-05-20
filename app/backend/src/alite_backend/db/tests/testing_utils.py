from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
import alite_backend
from alite_backend.db.db_session import get_engine_url
from alite_backend.db.models import Base 
from alite_backend.config import settings
import logging

logger = logging.getLogger(__name__)

TEST_DB_NAME = "TEST_DB_NAME" # Get the name from settings

# Create a test-specific engine
TEST_ENGINE = create_engine(get_engine_url(TEST_DB_NAME))
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

def get_test_db():
    """Dependency override for test cases to get a session on the test DB."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_test_db():
    """Drops and re-creates tables in the test database."""
    logger.info(f"Setting up test database: {TEST_DB_NAME}...")
    
    # 1. Drop all tables
    Base.metadata.drop_all(bind=TEST_ENGINE)
    
    # 2. Create all tables
    Base.metadata.create_all(bind=TEST_ENGINE)
    
    logger.info("Test database setup complete.")

def teardown_test_db():
    """Drops all tables in the test database (optional, run after tests)."""
    logger.info(f"Tearing down test database: {TEST_DB_NAME}...")
    Base.metadata.drop_all(bind=TEST_ENGINE)
    logger.info("Test database teardown complete.")