import pytest
import json
from uuid import UUID
from alite_backend.words.load import Loader
from alite_backend.db.schemas import ProcessedPayload
from alite_backend.db.models import Lemma, EnumVerbType, LessonList
from alite_backend.words.funcs import load_json

loader_test_loc = "/Users/aaron.thompson/code/alite/app/backend/src/alite_backend/db/tests/loader_test.json"

# Import your isolated_db fixture from conftest.py
def test_loader_successfully_inserts_data(isolated_db):
    
    # 2. SEED THE MISSING CONFIGURATION ROW
    # Justification: Because our ETL pipeline maps vocabulary terms against existing lesson structures,
    # we must guarantee that a lesson row matching name 'I' exists inside the SQLite runtime bounds.
    mock_lesson = LessonList(
        title="I",
        topic="Core Introductory Curriculum Block"
    )
    isolated_db.add(mock_lesson)
    isolated_db.commit() # Flush this configuration safely into our active RAM state
    
    # ARRANGE: Manually construct a pristine ProcessedPayload.
    loader = Loader(db_session=isolated_db)
    
    with open(loader_test_loc, 'r') as file:
        data = json.load(file)

    # Create a mock payload mimicking what `ReturnedLemmaProcessor` would output
    mock_payload = ProcessedPayload(**data)
    
    # ACT: Attempt to load the payload into the database
    loader.load_payload(mock_payload)
    
    # ASSERT: Query the database directly to ensure the records were created
    
    saved_lemma = isolated_db.query(Lemma).filter(Lemma.lem_text == "требовать").first()
    assert saved_lemma is not None
    assert saved_lemma.pos.value == "verb"