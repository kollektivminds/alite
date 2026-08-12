# create class for generating word-level questions

import logging
from functools import wraps
from typing import List, Optional, Sequence
from uuid import UUID

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
from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    NoResultFound,
    ProgrammingError,
    SQLAlchemyError,
    StatementError,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


#
# EXERCISES
#


class CRUDExercises(CRUDBase[Exercise, ExerciseCreate, ExerciseUpdate]):
    pass


crud_exercise = CRUDExercises(Exercise)

#
# ITEMS
#


class CRUDItems(CRUDBase[Item, ItemCreate, ItemUpdate]):
    pass


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
