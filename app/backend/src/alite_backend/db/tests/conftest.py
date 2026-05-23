# app/backend/src/alite_backend/db/tests/conftest.py
import pytest
import random
from alite_backend.db import models, schemas
from alite_backend.db.db_session import SessionLocal
from alite_backend.db.tests.factories import UserFactory, ExerciseFactory, ItemResponseFactory

# Fixture to inject a database session into any test function
@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
    
@pytest.fixture
def simulate_mcq_guess(db_session):
    
    def _simulate(ex_id: int):
        # latest question
        real_item = (
            db_session.query(models.Item)
            .filter(models.Item.in_ex == ex_id)
            .order_by(models.Item.id.desc())
            .first()
        )
        
        if not real_item:
            raise ValueError("No items found in the DB")
        
        # simulate student answer
        random_guess = random.choice(real_item.distractors | real_item.key)
        
        # check if correct
        is_correct = (random_guess == real_item.key)
        
        # make response
        response_record = ItemResponseFactory(
            ex_id=ex_id,
            item_id=real_item.id,
            student_answer=random_guess,
            is_correct=is_correct
        )
        
        return response_record
    
    return _simulate