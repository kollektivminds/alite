from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import List, Any
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.crud import sent_crud
from alite_backend.api import deps

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{sentence_id}", response_model=schemas.SentenceReturn)
def read_sentence(sentence_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific sentence by ID."""
    sentence = sent_crud.crud_sentence.get(db=db, id=sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return sentence


@router.get("/{sentence_id}/tokens", response_model=List[schemas.SentenceTokenReturn])
def get_sentence_tokens(sentence_id: int, db: Session = Depends(deps.get_db)):

    sentence = sent_crud.crud_sentence.get(db=db, id=sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence tokens not found")

    # lemmas = db.query(models.Lemma).filter(models.Lemma.in_less_list == lesson_id).all()
    return sentence.tokens
