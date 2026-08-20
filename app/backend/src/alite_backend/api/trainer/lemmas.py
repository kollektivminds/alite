from alite_backend.api import deps
from alite_backend.db import schemas
from alite_backend.db.crud.word_crud import crud_lemma
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", response_model=schemas.LemmaDetailsReturn)  # Uses your schemas.py
def create_lemma(
    lemma_in: schemas.LemmaCreate,
    db: Session = Depends(deps.get_db),
    # current_user = Depends(deps.get_current_active_user)
):

    return crud_lemma.create(db=db, obj_in=lemma_in)  # Calls your sentence_data.py


@router.get("/{lemma_id}", response_model=schemas.LemmaDetailsReturn)
def read_lemma(lemma_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific lemma by ID."""
    lemma = crud_lemma.get(db=db, id=lemma_id)
    if not lemma:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return lemma
