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
from alite_backend.db.models import (
    Item,
    Exercise,
    ItemResponse,
    ResponseResult
)
from alite_backend.db.schemas import (
    ItemCreate,
    ItemUpdate
)
from alite_backend.db.crud.crud_base import CRUDBase

logger = logging.getLogger(__name__)

#
# ITEMS
#


class CRUDItems(CRUDBase[Item, ItemCreate, ItemCreate]):
    pass


crud_item = CRUDItems(Item)