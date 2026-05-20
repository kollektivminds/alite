# generate class for users
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
    User, UserGroup, UserInGroup, EnumUserRole
)
from alite_backend.db.schemas import (
    UserCreate,
    UserUpdate,
    UserGroupCreate,
    UserGroupUpdate,
    UserInGroupCreate,
    UserInGroupUpdate,
)
from alite_backend.words.funcs import remove_accents
from alite_backend.db.crud.crud_base import CRUDBase

logger = logging.getLogger(__name__)

