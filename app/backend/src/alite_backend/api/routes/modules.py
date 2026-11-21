# alite_backend/api/trainer/modules.py
import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.crud import orgi_crud

router = APIRouter(prefix="/modules", tags=["modules"])

logger = logging.getLogger(__name__)


@router.get("/hierarchy", response_model=List[schemas.CurriculumModuleSummary])
def get_curriculum_hierarchy(
    db: Session = Depends(deps.get_db),  # noqa: B008
    _current_user: models.User = Depends(deps.get_current_user),  # noqa: B008
) -> List[schemas.CurriculumModuleSummary]:
    """
    Returns modules and their linked lessons/lists without loading vocabulary lemmas,
    keeping analytics scope selectors lightweight and fast.
    """
    # join module -> lessonlistinmodule -> lessonlist via sqlalchemy 2.0 select()
    stmt = (
        select(models.Module, models.LessonList)
        .join(
            models.LessonListInModule,
            models.LessonListInModule.mod_id == models.Module.id,  # type: ignore[arg-type]
        )
        .join(
            models.LessonList,
            models.LessonList.id == models.LessonListInModule.less_list_id,  # type: ignore[arg-type]
        )
        .order_by(models.Module.id, models.LessonList.id)  # type: ignore
    )

    grouped: Dict[int, tuple[str, List[schemas.CurriculumLessonSummary]]] = defaultdict(
        lambda: ("", [])
    )

    for mod, less_list in db.execute(stmt).all():
        if mod.id is None or less_list.id is None:
            continue
        mod_title = (
            getattr(mod, "name", None)
            or getattr(mod, "title", None)
            or f"Module {mod.id}"
        )
        lesson_label = (
            getattr(less_list, "title", None)
            or getattr(less_list, "name", None)
            or f"Lesson {less_list.id}"
        )
        _, existing_lessons = grouped[mod.id]
        existing_lessons.append(
            schemas.CurriculumLessonSummary(id=less_list.id, label=lesson_label)
        )
        grouped[mod.id] = (mod_title, existing_lessons)

    return [
        schemas.CurriculumModuleSummary(
            module_id=mod_id,
            module_name=mod_name,
            lessons=lessons,
        )
        for mod_id, (mod_name, lessons) in grouped.items()
    ]


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
            models.LessonListInModule.less_list_id
            == models.LemmaInLessonList.less_list_id,  # type: ignore
        )
        .where(models.LessonListInModule.mod_id == module_id)  # type: ignore
        .distinct()
    )

    lemmas = db.scalars(stmt).unique().all()

    return lemmas
