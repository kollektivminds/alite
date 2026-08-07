from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import List
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.crud import sent_crud
from alite_backend.api import deps

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{document_id}", response_model=schemas.DocumentReturn)
def read_document(document_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific document by ID."""
    document = sent_crud.crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/sentences", response_model=List[schemas.SentenceReturn])
def get_document_tokens(document_id: int, db: Session = Depends(deps.get_db)):

    document = sent_crud.crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document sentences not found")

    # lemmas = db.query(models.Lemma).filter(models.Lemma.in_less_list == lesson_id).all()
    return document.sentences
