# app/backend/api/routes/analytics.py
import logging

from fastapi import APIRouter, Depends, HTTPException, status
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
    db: Session = Depends(deps.get_db),  # noqa: B008
    current_user: models.User = Depends(deps.get_current_user),  # noqa: B008
) -> schemas.StudentDashboardSummary:
    """Returns personal BKT mastery, retention risk, and first-attempt accuracy."""
    assert current_user.id is not None  # noqa: S101
    return build_student_dashboard(db=db, user_id=current_user.id)


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
