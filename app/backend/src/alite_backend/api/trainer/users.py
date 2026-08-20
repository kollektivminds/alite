from alite_backend.api import deps
from alite_backend.db import schemas
from alite_backend.db.crud.user_crud import crud_user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/{user_id}", response_model=schemas.UserReturn)
def read_user(user_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific user by ID."""
    user = crud_user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user
