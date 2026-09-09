from alite_backend.api import deps
from alite_backend.db import models, schemas
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


@router.get("/settings", response_model=schemas.UserSettings)
def get_user_settings(current_user: models.User = Depends(deps.get_current_user)):
    """
    Returns user default settings from the JSONB column.
    Falls back to system-wide defaults if settings are empty.
    """
    default_config = {
        "difficulty": models.EnumItemDifficulty.MEDIUM,
        "theme": models.EnumSystemTheme.SYSTEM,
        "reduce_motion": True,
        "language": models.EnumTargetLanguage.EN,
    }
    return current_user.settings or default_config


@router.patch("/settings")
def update_user_settings(
    settings_update: dict,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Updates the JSONB settings payload for the current instructor.
    """
    current_settings = dict(current_user.settings or {})
    current_settings.update(settings_update)
    current_user.settings = current_settings
    db.commit()
    return current_user.settings
