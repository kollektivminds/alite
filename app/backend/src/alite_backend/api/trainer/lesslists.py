import logging
from typing import List

from alite_backend.api import deps
from alite_backend.db import schemas
from alite_backend.db.crud import orgi_crud
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{lesslist_id}", response_model=schemas.LessonListReturn)
def read_lesslist(lesslist_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific sentence by ID."""
    lesslist = orgi_crud.crud_less_list.get(db=db, id=lesslist_id)
    if not lesslist:
        raise HTTPException(status_code=404, detail="lesslist not found")
    return lesslist


@router.get("/{lesslist_id}/lemmas", response_model=List[schemas.LemmaDetailsReturn])
def get_lemmas_for_lesslist(lesslist_id: int, db: Session = Depends(deps.get_db)):

    lesslist = orgi_crud.crud_less_list.get(db=db, id=lesslist_id)
    if not lesslist:
        raise HTTPException(status_code=404, detail="lesslist lemmas not found")

    # lemmas = db.query(models.Lemma).filter(models.Lemma.in_less_list == lesslist_id).all()
    return lesslist.has_lemma
