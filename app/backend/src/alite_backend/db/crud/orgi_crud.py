import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
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
from alite_backend.db.crud.crud_base import CRUDBase

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

    def get_id_by_name(self, db: Session, less_list_name: str) -> int | None:
        stmt = select(self.model).where(self.model.title == less_list_name)
        result = db.scalars(stmt).first()
        if result is None:
            return None
        return result.id  # type: ignore


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
