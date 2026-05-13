from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from alite_backend.db import schemas, models
from alite_backend.db.crud import orgi_crud, word_crud
from alite_backend.api import deps

router = APIRouter()

# @router.post("/", response_model=schemas.SentenceResponse) # Uses your schemas.py
# def create_sentence(
#     sentence_in: schemas.SentenceCreate,
#     db: Session = Depends(deps.get_db),
#     current_user = Depends(deps.get_current_active_user)
# ):
#     """Create a new Russian sentence entry for analysis."""
#     return sentence_data.create(db=db, obj_in=sentence_in) # Calls your sentence_data.py

@router.get("/{lesson_id}", response_model=schemas.LessonListReturn)
def read_lesson(
    lesson_id: int, 
    db: Session = Depends(deps.get_db)
):
    """Fetch a specific sentence by ID."""
    lesson = orgi_crud.crud_less_list.get(db=db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Sentence not found")
    return lesson

@router.get("/{lesson_id}/lemmas", response_model=List[schemas.LemmaDetailsReturn])
def get_lemmas_for_lesson(lesson_id: int, db: Session = Depends(deps.get_db)):
    
    lesson = orgi_crud.crud_less_list.get(db=db, id=lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Sentence not found")
    
    #lemmas = db.query(models.Lemma).filter(models.Lemma.in_less_list == lesson_id).all()
    return lesson.has_lemma