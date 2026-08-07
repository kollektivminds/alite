from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import List
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.crud import orgi_crud
from alite_backend.api import deps

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{lesson_id}", response_model=schemas.LessonListReturn)
def read_lesson(lesson_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific sentence by ID."""
    lesson = orgi_crud.crud_less_list.get(db=db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.get("/{lesson_id}/lemmas", response_model=List[schemas.LemmaDetailsReturn])
def get_lemmas_for_lesson(lesson_id: int, db: Session = Depends(deps.get_db)):

    lesson = orgi_crud.crud_less_list.get(db=db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson lemmas not found")

    # lemmas = db.query(models.Lemma).filter(models.Lemma.in_less_list == lesson_id).all()
    return lesson.has_lemma
