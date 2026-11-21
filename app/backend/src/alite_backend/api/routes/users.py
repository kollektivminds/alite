# alite_backend/api/trainer/users.py
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.crud.user_crud import crud_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def _fetch_user_groups(db: Session, user_id: int) -> List[schemas.UserGroupMembership]:
    """Queries enrolled UserGroup rows for `user_id` using SQLAlchemy 2.0 select()."""
    stmt = (
        select(models.UserGroup)
        .join(
            models.UserInGroup,
            models.UserInGroup.group_id == models.UserGroup.id,  # type: ignore[arg-type]
        )
        .where(models.UserInGroup.user_id == user_id)  # type: ignore[arg-type]
        .order_by(models.UserGroup.group_name)
    )
    groups = list(db.scalars(stmt).all())
    return [
        schemas.UserGroupMembership(id=g.id, group_name=g.group_name)
        for g in groups
        if g.id is not None
    ]


@router.get(
    "/me", response_model=schemas.UserMeResponse, status_code=status.HTTP_200_OK
)
def read_current_user_profile(
    db: Session = Depends(deps.get_db),  # noqa: B008
    current_user: models.User = Depends(deps.get_current_user),  # noqa: B008
) -> schemas.UserMeResponse:
    """
    Returns the authenticated user's profile metadata, canonical role, and group memberships.
    Shared by AuthContext (for role-aware analytics) and the user profile screen.
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user session.",
        )

    memberships = _fetch_user_groups(db=db, user_id=int(current_user.id))

    return schemas.UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        alias=current_user.alias,
        created_at=current_user.created_at,
        groups=memberships,
    )


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
