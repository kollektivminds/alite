# alite_backend/api/trainer/lesslists.py
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.crud import orgi_crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lesslists", tags=["lesslists"])


@router.get("/all", response_model=List[schemas.LessonListReturn])
def read_lesson_lists(
    skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)
):
    """
    GET /lesson-lists
    Fetches curriculum modules for the frontend assessment configuration menu.
    """
    lesson_lists = orgi_crud.crud_less_list.get_multi(db=db)

    if not lesson_lists:
        return []

    return lesson_lists


@router.get("/options", response_model=List[schemas.LessonListSummaryOption])
def read_lesson_list_options(
    db: Session = Depends(deps.get_db),  # noqa: B008
) -> List[schemas.LessonListSummaryOption]:
    """
    Returns lesson/list IDs, names, and optional module IDs without loading lemma vocab,
    keeping analytics scope dropdowns fast and lightweight.
    """
    # Query LessonList outer-joined with LessonListInModule so lessons outside a module still appear.
    stmt = (
        select(models.LessonList, models.LessonListInModule.mod_id)  # type: ignore
        .outerjoin(
            models.LessonListInModule,
            models.LessonListInModule.less_list_id == models.LessonList.id,  # type: ignore[arg-type]
        )
        .order_by(models.LessonList.id)
    )

    options: List[schemas.LessonListSummaryOption] = []
    for less_list, mod_id in db.execute(stmt).all():
        if less_list.id is not None:
            label = (
                getattr(less_list, "title", None)
                or getattr(less_list, "name", None)
                or f"Lesson {less_list.id}"
            )
            options.append(
                schemas.LessonListSummaryOption(
                    id=less_list.id,
                    name=label,
                    module_id=mod_id,
                )
            )
    return options


@router.get("/{lesslist_id}", response_model=schemas.LessonListReturn)
def read_lesslist(lesslist_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific sentence by ID."""
    lesslist = orgi_crud.crud_less_list.get(db=db, id=lesslist_id)
    if not lesslist:
        raise HTTPException(status_code=404, detail="lesslist not found")
    return lesslist


@router.get("/{lesslist_id}/lemmas", response_model=List[schemas.LemmaDetailsReturn])
def get_lemmas_for_lesslist(lesslist_id: int, db: Session = Depends(deps.get_db)):

    lesslist = orgi_crud.crud_less_list.get(db=db, id=lesslist_id)
    if not lesslist:
        raise HTTPException(status_code=404, detail="lesslist lemmas not found")

    return lesslist.has_lemma
