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
    LessonList,
    LemmaInLessonList,
    LessonListInModule,
    Module,
)
from alite_backend.db.schemas import (
    ModuleCreate,
    ModuleUpdate,
    ModuleReturn,
    LessonListCreate,
    LessonListUpdate,
    LessonListReturn,
    LessListInModCreate,
    LessListInModUpdate,
    LessListInModReturn,
    LemInLessListCreate,
    LemInLessListUpdate,
)
from alite_backend.words.funcs import remove_accents
from alite_backend.db.crud.crud_base import CRUDBase
from alite_backend.db import models, schemas

logger = logging.getLogger(__name__)

#
# MODULES
#


class CRUDModule(CRUDBase[Module, ModuleCreate, ModuleUpdate]):
    pass


crud_module = CRUDModule(Module)


#
# LESSONS & LISTS
#


class CRUDLessList(CRUDBase[LessonList, LessonListCreate, LessonListUpdate]):

    def get_id_by_name(self, db: Session, less_list_name: str) -> int:
        stmt = select(self.model).where(self.model.title == less_list_name)
        # return db.query(self.model).filter(self.model.title == less_list_name).first().id  # type: ignore
        return db.scalars(stmt).first().id  # type: ignore


crud_less_list = CRUDLessList(LessonList)


#
# LESSONS & LISTS IN MODULES
#


class CRUDLessListInMod(
    CRUDBase[LessonListInModule, LessListInModCreate, LessListInModUpdate]
):
    pass


crud_less_list_in_mod = CRUDLessListInMod(LessonListInModule)

#
# LEMMAS IN LESSONS & LISTS
#


class CRUDLemInLessList(
    CRUDBase[LemmaInLessonList, LemInLessListCreate, LemInLessListUpdate]
):
    pass


crud_lem_in_less_list = CRUDLemInLessList(LemmaInLessonList)
