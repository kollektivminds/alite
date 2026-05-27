# app/backend/src/alite_backend/db/tests/conftest.py
import pytest
import random
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from alite_backend.config import settings
from alite_backend.db import models, schemas
from alite_backend.main import app
from alite_backend.db import models
from alite_backend.db.db_session import get_db
from alite_backend.db.db_session import SessionLocal
from alite_backend.db.tests.factories import UserFactory, ExerciseFactory, ItemResponseFactory


# 1. DEFINE URI STRINGS Explicitly
DEV_DATABASE_URL = str(settings.DEV_DATABASE_URL)
TEST_DATABASE_URL = str(settings.TEST_DATABASE_URL)

dev_engine = create_engine(DEV_DATABASE_URL)
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def clone_lexicon_snapshot():
    """
    SESSION SCOPE: Runs once at test initiation.
    Bridges live developmental database tables over to our isolated sandbox.
    """
    # Clear out older testing residues and spin up the complete schema
    models.Base.metadata.drop_all(bind=test_engine)
    models.Base.metadata.create_all(bind=test_engine)

    # Reflect the architecture of the development engine
    dev_metadata = MetaData()
    dev_metadata.reflect(bind=dev_engine)
    
    lexicon_tables = ["lemmas", "lexicon", "gram_props", "word_forms", "definitions"]
    
    dev_conn = dev_engine.connect()
    test_conn = test_engine.connect()
    
    try:
        for table_name in lexicon_tables:
            if table_name in dev_metadata.tables:
                table = dev_metadata.tables[table_name]
                # Read structural information directly from dev database
                records = dev_conn.execute(select(table)).fetchall()
                
                if records:
                    # Convert raw records into pure dictionary structures
                    insert_payload = [dict(row._mapping) for row in records]
                    # Bulk insert directly into the corresponding placeholder tables
                    test_conn.execute(table.insert(), insert_payload)
        test_conn.commit()
    finally:
        dev_conn.close()
        test_conn.close()


@pytest.fixture(scope="function")
def db_session(clone_lexicon_snapshot):
    """
    FUNCTION SCOPE: Protects the snapshot database by executing every test 
    inside an uncommitted database transaction savepoint.
    """
    connection = test_engine.connect()
    # Establish isolation barrier
    transaction = connection.begin()
    
    # Bind runtime session to this transaction lifecycle
    session = TestingSessionLocal(bind=connection)
    
    yield session  # Testing functions populate dynamic items here
    
    # Teardown: Close the session and ROLL BACK the transaction.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def api_client(db_session):
    """
    Overrides the FastAPI dependency injection container so route logic executes
    directly inside our uncommitted transaction pool.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()