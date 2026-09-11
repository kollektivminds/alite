import http
import logging
import unicodedata

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.services import exercise_router, flashcard_generator
from alite_backend.services.exercise_router import ExerciseRouter
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import false, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=schemas.ExerciseResponse)
async def create_custom_exercise(
    http_request: Request,
    request: schemas.ExerciseRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    try:
        raw_body = await http_request.json()
        logger.info(f"Incoming /generate payload structure: {raw_body}")
    except Exception as parse_err:
        logger.warning(f"Failed to decode incoming request body as JSON: {parse_err}")

    generator = ExerciseRouter(
        db=db,
        user_id=current_user.id,
        # exercise_request = request
    )
    return generator.generate_exercise(request=request)


def normalize_token(text: str) -> str:
    """
    Normalizes Cyrillic strings by decomposing accents, removing combining
    diacritics (stress marks), and case-folding to avoid false-negative evaluations.
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text.strip())
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped).casefold()


def check_answer(
    db: Session,
    item_id: int,
    submitted_answer: str,
) -> bool:
    """
    Evaluates set membership against stored options marked correct for this item.
    """
    key_stmt = (
        select(models.ItemOption.option_text)
        .where(models.ItemOption.item_id == item_id)
        .where(models.ItemOption.is_correct.is_(True))
    )
    keys = db.scalars(key_stmt).all()

    if not keys:
        logger.warning("Assessment item %d has no valid answer keys defined.", item_id)
        return False

    # normalize keys and submission to eliminate stress-mark mismatches
    normalized_keys = {normalize_token(k) for k in keys}
    return normalize_token(submitted_answer) in normalized_keys


@router.post(
    "/evaluate",
    response_model=schemas.AnswerResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate student submission and log psychometric response data",
)
async def evaluate_student_answer(
    submission: schemas.AnswerSubmission,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.AnswerResult:
    # verify item existence
    item_exists = db.scalar(
        select(models.Item.id).where(models.Item.id == submission.item_id)
    )
    if not item_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {submission.item_id} not found.",
        )

    # evaluate answer against database keys
    is_correct = check_answer(
        db=db, item_id=submission.item_id, submitted_answer=submission.response
    )

    # 3. Persist item telemetry linked to the active learner
    response_record = models.ItemResponse(
        user_id=current_user.id,
        item_id=submission.item_id,
        response=submission.response.strip(),
        is_correct=is_correct,
        response_time_ms=max(0, submission.response_time_ms),
        attempt_num=submission.attempt_num,
    )
    db.add(response_record)
    db.commit()

    return schemas.AnswerResult(is_correct=is_correct)
