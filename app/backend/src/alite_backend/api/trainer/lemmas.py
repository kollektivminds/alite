from typing import List

from alite_backend.api import deps
from alite_backend.db import schemas
from alite_backend.db.crud.word_crud import crud_lemma
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", response_model=schemas.LemmaDetailsReturn)  # Uses your schemas.py
def create_lemma(
    lemma_in: schemas.LemmaCreate,
    db: Session = Depends(deps.get_db),
    # current_user = Depends(deps.get_current_active_user)
):

    return crud_lemma.create(db=db, obj_in=lemma_in)  # Calls your sentence_data.py


@router.get("/search", response_model=List[schemas.LemmaDetailsReturn])
def search_lemmas_api(
    q: str = Query(
        ..., alias="q", min_length=2, description="The lemma text to search for"
    ),
    db: Session = Depends(deps.get_db),
):
    try:
        results = crud_lemma.search_lemmas_fuzzy(db, query_str=q)
        return results
    except Exception as e:
        # Prevents internal DB errors from leaking, but alerts the frontend
        raise HTTPException(
            status_code=500, detail="Database search encountered an error."
        )


@router.get("/{lemma_id}", response_model=schemas.LemmaDetailsReturn)
def read_lemma(lemma_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific lemma by ID."""
    lemma = crud_lemma.get(db=db, id=lemma_id)
    if not lemma:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return lemma
