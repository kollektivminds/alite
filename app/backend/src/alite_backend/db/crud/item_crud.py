# create class for generating word-level questions

import logging
from typing import List

from alite_backend.api import deps
from alite_backend.db.crud.crud_base import CRUDBase
from alite_backend.db.models import Exercise, Item, ItemOption, ItemResponse
from alite_backend.db.schemas import (
    ExerciseCreate,
    ExerciseUpdate,
    ItemCreate,
    ItemOptionCreate,
    ItemOptionUpdate,
    ItemResponseCreate,
    ItemResponseUpdate,
    ItemUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

#
# EXERCISES
#


class CRUDExercises(CRUDBase[Exercise, ExerciseCreate, ExerciseUpdate]):

    def get_exercise_record(
        self,
        db: Session,
        user=Depends(deps.get_current_user),
        limit: int = 50,
    ):
        # current_user_id = user.id
        # stmt = (
        #     select(self.model).where(Exercise.user_id == current_user_id).limit(limit)
        # )
        return user  # list(db.scalars(stmt).all())


crud_exercise = CRUDExercises(Exercise)

#
# ITEMS
#


class CRUDItems(CRUDBase[Item, ItemCreate, ItemUpdate]):

    def get_completed_items(
        self,
        db: Session,
        user_id: int = Depends(deps.get_current_user),
        limit: int = 50,
    ):

        return all_results


crud_item = CRUDItems(Item)


#
# ITEM OPTIONS
#


class CRUDItemOptions(CRUDBase[ItemOption, ItemOptionCreate, ItemOptionUpdate]):
    pass


crud_item_option = CRUDItemOptions(ItemOption)


#
# ITEM RESPONSES
#


class CRUDItemResponses(CRUDBase[ItemResponse, ItemResponseCreate, ItemResponseUpdate]):
    pass


crud_item_response = CRUDItemResponses(ItemResponse)
