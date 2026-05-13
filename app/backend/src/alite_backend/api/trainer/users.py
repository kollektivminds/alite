from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from alite_backend.db import schemas
from alite_backend.db.crud import user_crud
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

# @router.get("/{sentence_id}", response_model=schemas.SentenceResponse)
# def read_sentence(
#     sentence_id: int, 
#     db: Session = Depends(deps.get_db)
# ):
#     """Fetch a specific sentence by ID."""
#     sentence = sentence_data.get(db=db, id=sentence_id)
#     if not sentence:
#         raise HTTPException(status_code=404, detail="Sentence not found")
#     return sentence