# conftest.py

import pytest
from app.backend.db.testing_utils import setup_test_db, get_test_db

# Fixture to run before all tests to initialize the DB
@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_db():
    # Setup runs before all tests in the session
    setup_test_db()
    
    # Yield control to the tests
    yield
    
    # Teardown runs after all tests in the session (optional cleanup)
    # teardown_test_db() 

# Fixture to inject a database session into any test function
@pytest.fixture(scope="function")
def db_session():
    # This automatically calls setup_and_teardown_db() if used.
    # We use the generator from testing_utils to manage the session.
    yield from get_test_db()

# Example Test File (e.g., test_crud.py)
# You can now write tests that are fast and isolated:

# from app.backend.db.crud import word_data
# from app.backend.db.schemas import WordCreate

# def test_create_word(db_session): # Pytest injects the db_session fixture
#     new_word = word_data.create_word(
#         db=db_session, 
#         word_in=WordCreate(lemma="test", pos="NOUN", frequency=10)
#     )
#     assert new_word.lemma == "test"
#     assert word_data.get_word_by_lemma(db_session, "test") is not None