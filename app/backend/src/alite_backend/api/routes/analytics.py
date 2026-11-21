# app/backend/api/routes/analytics.py
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.services.analytics import (
    build_admin_platform_summary,
    build_class_analytics,
    build_student_dashboard,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/analytics", tags=["analytics"])


def _require_roles(user: models.User, allowed_roles: set[models.EnumUserRole]) -> None:
    """Enforces explicit role membership before returning cohort or admin analytics."""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this analytics view.",
        )


@router.get("/student/me", response_model=schemas.StudentDashboardSummary)
def get_my_student_analytics(
    # Optional curriculum filters narrow StudentKSAState rollups to lemmas in a module
    # and/or lesson list; omitting both returns overall learner mastery[cite: 2, 25].
    module_id: Optional[int] = Query(
        default=None,
        ge=1,
        description="Optional Module ID to scope vocabulary KSA mastery and retention.",
    ),
    lesson_id: Optional[int] = Query(
        default=None,
        ge=1,
        description="Optional LessonList ID to scope vocabulary KSA mastery and retention.",
    ),
    include_non_lemma_states: bool = Query(
        default=False,
        description="Include states with lemma_id IS NULL when a module/lesson scope is active.",
    ),
    db: Session = Depends(deps.get_db),  # noqa: B008
    current_user: models.User = Depends(deps.get_current_user),  # noqa: B008
) -> schemas.StudentDashboardSummary:
    """
    Returns personal BKT mastery, Ebbinghaus retention, ZPD focus suggestions,
    and domain rollups for the authenticated learner[cite: 15, 25].
    """
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user session.",
        )

    # Delegate filtering and statistical aggregation to the service layer.
    return build_student_dashboard(
        db=db,
        user_id=current_user.id,
        module_id=module_id,
        lesson_id=lesson_id,
        include_non_lemma_states=include_non_lemma_states,
    )


@router.get(
    "/instructor/class/{group_id}", response_model=schemas.ClassAnalyticsSummary
)
def get_instructor_class_analytics(
    group_id: int,
    db: Session = Depends(deps.get_db),  # noqa: B008
    current_user: models.User = Depends(deps.get_current_user),  # noqa: B008
) -> schemas.ClassAnalyticsSummary:
    """Returns class-level KSA mastery and learner roster for instructors and admins."""
    _require_roles(
        current_user,
        {models.EnumUserRole.INSTRUCTOR, models.EnumUserRole.ADMIN},
    )
    summary = build_class_analytics(db=db, group_id=group_id)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User group {group_id} not found.",
        )
    return summary


@router.get("/admin/overview", response_model=schemas.AdminPlatformSummary)
def get_admin_platform_analytics(
    db: Session = Depends(deps.get_db),  # noqa: B008
    current_user: models.User = Depends(deps.get_current_user),  # noqa: B008
) -> schemas.AdminPlatformSummary:
    """Returns platform-wide usage and KSA coverage metrics for administrators."""
    _require_roles(current_user, {models.EnumUserRole.ADMIN})
    return build_admin_platform_summary(db=db)
