# app/backend/src/alite_backend/db/tests/conftest.py
import json

import pytest
from alite_backend.api import deps
from alite_backend.config import settings
from alite_backend.db import models, schemas
from alite_backend.db.tests.factories import ALL_FACTORIES, BaseFactory, UserFactory
from alite_backend.main import app
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import ARRAY

# # GLOBAL DIALECT COMPILER OVERRIDES
# @compiles(ARRAY, "sqlite")
# def compile_array_sqlite(type_, compiler, **kw):
#     """DDL PHASE: Forces SQLite to render ARRAY columns as TEXT definitions."""
#     return "TEXT"


# # Save references to SQLAlchemy's original internal array serialization routines
# _orig_bind_processor = ARRAY.bind_processor
# _orig_result_processor = ARRAY.result_processor

# def sqlite_compatible_bind_processor(self, dialect):
#     """
#     DML WRITE PHASE: Intercepts list objects bound for the database.
#     If the active engine is SQLite, serialize lists to JSON strings so the driver
#     doesn't crash. Otherwise, fall back to Postgres native array transport.
#     """
#     if dialect.name == "sqlite":
#         def process(value):
#             if value is not None:
#                 return json.dumps(value)
#             return None
#         return process
#     return _orig_bind_processor(self, dialect)

# def sqlite_compatible_result_processor(self, dialect, coltype):
#     """
#     DML READ PHASE: Intercepts strings coming out of database queries.
#     If the engine is SQLite, parse stored JSON text back into pristine Python lists.
#     """
#     if dialect.name == "sqlite":
#         def process(value):
#             if value is not None:
#                 try:
#                     return json.loads(value)
#                 except json.JSONDecodeError:
#                     return []
#             return []
#         return process
#     return _orig_result_processor(self, dialect, coltype)

# # Prepend our behavior adaptations globally into the SQLAlchemy type class tree
# ARRAY.bind_processor = sqlite_compatible_bind_processor
# ARRAY.result_processor = sqlite_compatible_result_processor

try:
    # 1. Handle DDL Table Compilation Bounds
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.types import ARRAY

    @compiles(ARRAY, "sqlite")
    def compile_array_sqlite(type_, compiler, **kw):
        """Forces SQLite to compile abstract ARRAY fields as simple TEXT blocks."""
        return "TEXT"

    # Also handle the Postgres dialect explicit class definition just in case it was imported directly
    from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

    @compiles(PG_ARRAY, "sqlite")
    def compile_pg_array_sqlite(type_, compiler, **kw):
        return "TEXT"

except ImportError:
    pass


# 2. Handle DML Parameter Binding Bounds (The Driver Safety Net)
# Justification: Setting retval=True allows this function to replace query arguments
# dynamically in memory immediately before Python hands them to the database cursor.
@event.listens_for(Engine, "before_cursor_execute", retval=True)
def convert_complex_types_for_sqlite(
    conn, cursor, statement, parameters, context, executemany
):
    """
    Universally intercepts database bindings during test runtime execution.
    If running on SQLite, it safely coerces lists/dicts into serialized JSON text.
    """
    if conn.dialect.name == "sqlite" and parameters:

        # Scenario A: Bulk Inserts (executemany = True)
        # Parameters will arrive structured inside a sequence list of configurations
        if executemany:
            new_parameters = []
            for param_set in parameters:
                if isinstance(param_set, dict):
                    new_parameters.append(
                        {
                            k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                            for k, v in param_set.items()
                        }
                    )
                elif isinstance(param_set, (list, tuple)):
                    new_parameters.append(
                        tuple(
                            json.dumps(v) if isinstance(v, (list, dict)) else v
                            for v in param_set
                        )
                    )
                else:
                    new_parameters.append(param_set)
            return statement, new_parameters

        # Scenario B: Single Row Inserts (executemany = False)
        else:
            # Handle dictionary-mapped named parameters (:param)
            if isinstance(parameters, dict):
                new_parameters = {
                    k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                    for k, v in parameters.items()
                }
                return statement, new_parameters

            # Handle sequential positional parameters (?) used by SQLite compilers
            elif isinstance(parameters, (list, tuple)):
                new_parameters = tuple(
                    json.dumps(v) if isinstance(v, (list, dict)) else v
                    for v in parameters
                )
                return statement, new_parameters

    # If the driver target dialect is PostgreSQL, bypass entirely to maintain native speed
    return statement, parameters


DEV_DATABASE_URL = str(settings.DEV_DATABASE_URL)
TEST_DATABASE_URL = str(settings.TEST_DATABASE_URL)

dev_engine = create_engine(DEV_DATABASE_URL)
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False)


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

    lexicon_tables = [
        "lemmas",
        "lexicon",
        "gram_props",
        "word_forms",
        "definitions",
        "examples",
        "pronunciations",
        "lem_rels",
        "lookup_queue",
        "lem_defs",
        "def_exs",
        "lem_prons",
        "modules",
        "lessons_lists",
        "lems_in_less_lists",
        "less_lists_in_mods",
    ]

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

    # Establish a savepoint
    # nested = session.begin_nested()

    # # Handle Application-Level Commits (The Magic)
    # @event.listens_for(session, "after_transaction_end")
    # def end_savepoint(session, transaction):
    #     nonlocal nested
    #     if not nested.is_active:
    #         nested = session.begin_nested()

    for factory_class in ALL_FACTORIES:
        factory_class._meta.sqlalchemy_session = session

    yield session  # Running tests populate transient items here

    # teardown: safely sever session pointers to prevent cross-test memory contamination
    for factory_class in ALL_FACTORIES:
        factory_class._meta.sqlalchemy_session = None
    # teardown: close the session and ROLL BACK the outer transaction.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def api_client(db_session):
    """
    Overrides the FastAPI dependency injection container so route logic executes
    directly inside our uncommitted transaction pool.
    """

    test_user = UserFactory()
    db_session.flush()

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
