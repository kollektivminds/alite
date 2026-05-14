# app/backend/src/alite_backend/services/flashcard_generator.py
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from alite_backend.db import models, schemas
import random
from sqlalchemy import text

def get_spelling_distractors(db: Session, target_lemma_text: str, limit: int = 3):
    """Fetches words spelled similarly to the target word to act as distractors."""
    distractors = (
        db.query(models.Lemma)
        .filter(models.Lemma.lem_text != target_lemma_text)
        # Order by similarity (requires pg_trgm extension)
        .order_by(models.Lemma.lem_text.op('<->')(target_lemma_text)) 
        .limit(limit)
        .all()
    )
    return distractors