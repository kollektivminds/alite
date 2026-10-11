# alite_backend/api/trainer/modules.py
import logging
from typing import List

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.crud import orgi_crud
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/{module_id}", response_model=schemas.ModuleReturn)
def read_module(module_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific sentence by ID."""
    module = orgi_crud.crud_module.get(db=db, id=module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@router.get("/{module_id}/lemmas", response_model=List[schemas.LemmaDetailsReturn])
def get_lemmas_for_lesson(module_id: int, db: Session = Depends(deps.get_db)):
    # check if the module actually exists
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    stmt = (
        select(models.Lemma)
        .join(
            models.LemmaInLessonList,
            models.Lemma.id == models.LemmaInLessonList.lem_id,  # type: ignore
        )
        .join(
            models.LessonListInModule,
            models.LessonListInModule.less_list_id == models.LemmaInLessonList.less_list_id,  # type: ignore
        )
        .where(models.LessonListInModule.mod_id == module_id)  # type: ignore
        .distinct()
    )

    lemmas = db.scalars(stmt).unique().all()

    return lemmas
