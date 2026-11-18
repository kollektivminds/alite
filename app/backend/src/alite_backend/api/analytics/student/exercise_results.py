import logging
import re
import unicodedata
from typing import Iterable, Optional, Set, Tuple

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.crud.item_crud import crud_exercise, crud_item
from alite_backend.services.exercise_router import ExerciseRouter
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import false, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history")
async def get_results_summary(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    # user_id = current_user.id
    user_exercises = crud_exercise.get_exercise_record(db=db)
    return user_exercises
