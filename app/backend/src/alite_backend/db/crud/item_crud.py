# create class for generating word-level questions

import logging
from typing import List, Optional, Sequence
from uuid import UUID
from functools import wraps
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    ProgrammingError,
    DBAPIError,
    NoResultFound,
    StatementError,
)
from fastapi import HTTPException, status
from alite_backend.db.crud.crud_base import CRUDBase
from alite_backend.db.models import Item, Exercise, ItemResponse
from alite_backend.db.schemas import (
    ItemCreate,
    ItemUpdate,
    ExerciseCreate,
    ExerciseUpdate,
    ItemResponseCreate,
    ItemResponseUpdate
)

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
# ITEM RESPONSES
#

class CRUDItemResponses(CRUDBase[ItemResponse, ItemResponseCreate, ItemResponseUpdate]):
    pass

crud_item_response = CRUDItemResponses(ItemResponse)