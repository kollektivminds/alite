import logging
from typing import List

from alite_backend.api import deps
from alite_backend.db import schemas
from alite_backend.db.crud.word_crud import crud_lemma
from alite_backend.db.models import Lemma
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=schemas.LemmaDetailsReturn)  # Uses your schemas.py
def create_lemma(
    lemma_in: schemas.LemmaCreate,
    db: Session = Depends(deps.get_db),
    # current_user = Depends(deps.get_current_active_user)
):

    return crud_lemma.create(db=db, obj_in=lemma_in)  # Calls your sentence_data.py


@router.get("/search", response_model=List[schemas.LemmaSearchResults])
def search_lemmas_api(
    q: str = Query(
        ..., alias="q", min_length=2, description="The lemma text (EN/RU) to search for"
    ),
    db: Session = Depends(deps.get_db),
) -> List[Lemma]:
    try:
        results = crud_lemma.search_lemmas_fuzzy(db, query_str=q)
        return results
    except Exception as exc:
        # 1. Output the complete stack trace directly to Docker container stdout
        logger.exception("Lemma search query failed for input '%s'", q)

        # 2. Bubble up the exact error detail during development so the frontend can inspect it
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database search error: {str(exc)}",
        ) from exc


@router.get("/{lemma_id}", response_model=schemas.LemmaDetailsReturn)
def read_lemma(lemma_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific lemma by ID."""
    lemma = crud_lemma.get(db=db, id=lemma_id)
    if not lemma:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return lemma
