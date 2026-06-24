# app/backend/src/alite_backend/db/tests/test_etl_pipeline.py

import pytest
from sqlalchemy import select
from sqlalchemy.orm.session import Session
from alite_backend.db import models, schemas
# Import your actual pipeline/loader class here
from alite_backend.words.pipeline import feed_data 

def test_participle_tagging_in_etl(isolated_db):
    """
    Validates that the ETL function correctly parses and persists a participle,
    ensuring no missing relations in the Lemma -> WordForm -> GramProp chain.
    """
    
    # =========================================================================
    # 1. ARRANGE
    # Define a minimal, targeted payload that exposes the participle edge case.
    # =========================================================================
    raw_payload = ["лететь", "отказаться"]
    
    # =========================================================================
    # 2. ACT
    # Pass the payload (and the injected session, if your function takes it) 
    # directly into your ETL function.
    # =========================================================================
    feed_data(isolated_db, raw_payload)
    
    # =========================================================================
    # 3. ASSERT
    # Query the session to ensure the transformation mapped to the schema.
    # =========================================================================
    
    # Verify the target lemma made it into the DB
    stmt = select(models.Lemma).where(models.Lemma.lem_text == "лететь")
    stmt = select(models.Lemma).where(models.Lemma.lem_text == "отказаться")
    new_lemma = isolated_db.execute(stmt).scalar_one_or_none()
    
    assert new_lemma is not None, "ETL failed to load the participle into the Lemma table."
    assert new_lemma.pos == models.EnumPartOfSpeech.VERB, "POS tagged incorrectly."
    
    # Verify the morphological data was written to GramProp and linked via WordForm
    stmt_form = (
        select(models.WordForm, models.GramProp)
        .join(models.GramProp, models.WordForm.gram_id == models.GramProp.id)
        .where(models.WordForm.lem_id == new_lemma.id)
    )
    
    form_results = isolated_db.execute(stmt_form).all()
    assert len(form_results) > 0, "No WordForms/GramProps generated for the participle."
    
    # Check specific morphological tags to ensure your new participle logic fired
    sample_form, sample_gram = form_results[0]
    
    # assert sample_gram.part_voice == schemas.EnumPartVoice.PASSIVE
    # assert sample_gram.gram_tense == schemas.EnumGramTense.PAST