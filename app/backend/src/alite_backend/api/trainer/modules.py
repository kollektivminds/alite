from fastapi import APIRouter, Depends, HTTPException
from typing import List
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from alite_backend.db import schemas, models
from alite_backend.db.crud import orgi_crud
from alite_backend.api import deps

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
    # 1. Check if the module actually exists
    #stmt = select(models.Module).where(models.Module.id == module_id)
    #module = db.query(models.Module).filter(models.Module.id == module_id).first()
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    stmt = (
        select(models.Lemma)
        .join(models.LemmaInLessonList,
              models.Lemma.id == models.LemmaInLessonList.lem_id
        )
        .join(
            models.LessonListInModule,
            models.LessonListInModule.less_list_id == models.LemmaInLessonList.less_list_id,
        )
        .where(models.LessonListInModule.mod_id == module_id)
        .distinct()
    )
    
    # lemmas = (
    #     db.query(models.Lemma)
    #     # join Lemma to its Lesson junction table
    #     .join(
    #         models.LemmaInLessonList, models.Lemma.id == models.LemmaInLessonList.lem_id
    #     )
    #     # join the Lesson junction table to the Module junction table
    #     .join(
    #         models.LessonListInModule,
    #         models.LessonListInModule.less_list_id
    #         == models.LemmaInLessonList.less_list_id,
    #     )
    #     # filter by the requested Module ID
    #     .filter(models.LessonListInModule.mod_id == module_id)
    #     # optional: Add .distinct() in case a lemma appears in multiple lessons within the same module
    #     .distinct().all()
    # )
    
    lemmas = db.scalars(stmt).unique().all()
    
    return lemmas
