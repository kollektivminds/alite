import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY
from uuid import uuid4
from alite_backend.main import app
from alite_backend.db import models


@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    """Tells SQLite to compile ARRAY() columns as TEXT fields behind the scenes."""
    return "TEXT"


sqlite_engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)


@pytest.fixture(scope="function")
def isolated_db():
    """Builds a fresh, empty schema in RAM for a single test."""
    models.Base.metadata.create_all(bind=sqlite_engine)
    session = SessionLocal()
    yield session
    session.close()
    models.Base.metadata.drop_all(bind=sqlite_engine)


def test_pytest_is_working():
    assert 2 + 2 == 4
    assert "ALITE".islower() is False


# -------------------------------------------------------------------------
# TEST 2: Testing ALITE Models in Isolation
# -------------------------------------------------------------------------
def test_can_save_and_retrieve_lemma(isolated_db):
    """
    ARRANGE: We have an empty, isolated database.
    ACT: We insert exactly one controlled Russian word.
    ASSERT: We verify SQLAlchemy can retrieve it.
    """
    # Create a perfectly controlled Lemma object
    test_lemma = models.Lemma(
        entry_key=uuid4(),
        lem_text="успех",
        pos="noun")  # Russian for "success"

    # Save to our in-memory database
    isolated_db.add(test_lemma)
    isolated_db.commit()

    # Query it back
    saved_lemma = isolated_db.query(models.Lemma).filter_by(lem_text="успех").first()

    # Verify the object made the round-trip successfully
    assert saved_lemma is not None
    assert saved_lemma.pos == "noun"


# -------------------------------------------------------------------------
# TEST 3: Testing FastAPI Routing (No Database)
# -------------------------------------------------------------------------
def test_app_is_routing_correctly():
    """
    Proves that your FastAPI application can boot up and respond to
    HTTP requests, regardless of the database state.
    """
    client = TestClient(app)

    # Hitting the auto-generated FastAPI docs endpoint is a safe way
    # to test routing without triggering database logic.
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
