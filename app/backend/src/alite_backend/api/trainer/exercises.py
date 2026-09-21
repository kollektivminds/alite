import logging
import re
import unicodedata
from typing import Iterable, Optional, Set, Tuple

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.services import exercise_router
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


def normalize_token(
    text: str, preserve_accents: bool = False, preserve_yo: bool = False
) -> str:
    """
    Deterministically normalizes a Cyrillic token for psychometric evaluation.

    Pipeline:
    1. Strips leading/trailing whitespace and collapses internal whitespace runs.
    2. Decomposes characters via Unicode Canonical Decomposition (NFD).
    3. Strips combining diacritical marks (Unicode category 'Mn', including \u0301 acute accent),
       unless preserve_accents is True.
    4. Applies case-folding for case-insensitive matching.
    5. Optionally normalizes 'ё' to 'е' to prevent false negatives.
    6. Re-composes characters back to Canonical Composition (NFC).
    """
    if not text:
        return ""

    # normalize whitespace
    cleaned = re.sub(r"\s+", " ", text.strip())

    # unicode NFD decomposition splits base characters from combining diacritics
    decomposed = unicodedata.normalize("NFD", cleaned)

    # strip combining diacritics (stress marks) if accents are not strictly tested
    if not preserve_accents:
        decomposed = "".join(
            ch for ch in decomposed if unicodedata.category(ch) != "Mn"
        )

    # standard case-folding (more aggressive and comprehensive than .lower() across locales)
    folded = decomposed.casefold()

    # interchangeable Russian 'ё' -> 'е' normalization
    if not preserve_yo:
        folded = folded.replace("ё", "е")

    # recompose to standard NFC representation
    return unicodedata.normalize("NFC", folded)


def evaluate_text_response(
    submitted_answer: str,
    acceptable_keys: Iterable[str],
    preserve_accents: bool = False,
) -> bool:
    """
    Evaluates a student's submission against an iterable of authorized keys.

    Performs a single-pass O(1) set-membership test over normalized representations,
    guaranteeing symmetry regardless of whether accents were passed via MCQ buttons
    or typed into a standard unaccented FITB input.
    """
    if not submitted_answer or not acceptable_keys:
        return False

    # normalize student input once
    normalized_submission = normalize_token(
        submitted_answer, preserve_accents=preserve_accents
    )

    # build the authorized lookup set in a single comprehension
    normalized_keys: Set[str] = {
        normalize_token(k, preserve_accents=preserve_accents)
        for k in acceptable_keys
        if k
    }

    # deterministic O(1) set membership check
    return normalized_submission in normalized_keys


def get_canonical_and_evaluation(
    db: Session, item_id: int, submitted_answer: str
) -> Tuple[bool, Optional[str]]:
    """
    Safely checks answer options for objective formats (MCQ, FITB).
    Guarantees a tuple return even if no options exist, preventing IndexErrors.
    """
    stmt = (
        select(models.ItemOption.option_text)
        .where(models.ItemOption.item_id == item_id)
        .where(models.ItemOption.is_correct.is_(True))
    )
    keys = db.scalars(stmt).all()

    if not keys:
        logger.warning("No correct keys found in db for item_id: %s", item_id)
        return False, None

    canonical_key = keys[0]
    # unified evaluation: handles accented MCQs and unaccented FITBs identically
    is_correct = evaluate_text_response(
        submitted_answer=submitted_answer,
        acceptable_keys=keys,
    )
    return is_correct, canonical_key


@router.post(
    "/evaluate",
    response_model=schemas.AnswerResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate student submission and log psychometric response data",
)
def evaluate_student_answer(
    submission: schemas.AnswerSubmission,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.AnswerResult:
    try:
        # verify item existence
        item = db.scalar(
            select(models.Item).where(models.Item.id == submission.item_id)
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {submission.item_id} not found.",
            )

        canonical_answer: Optional[str] = None
        logger.debug("Item format: %s", item.item_format)
        # polymorphic branching: Flashcards have no objective keys
        if item.item_format == models.EnumItemFormat.FLASHCARD:
            # map rating to BKT success threshold ('remembered' and 'mastered' count as positive recall)
            is_correct = submission.response.lower() in {"remembered", "mastered"}
            canonical_answer = None
        else:
            # objective verification against ItemOption
            is_correct, canonical_answer = get_canonical_and_evaluation(
                db=db, item_id=submission.item_id, submitted_answer=submission.response
            )

        # log response telemetry safely
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

        # reveal answer if item is correct or user exhausted attempts
        should_reveal = is_correct or getattr(submission, "is_final_attempt", False)

        return schemas.AnswerResult(
            is_correct=is_correct,
            correct_answer=canonical_answer if should_reveal else None,
            explanation=getattr(item, "explanation", None) if should_reveal else None,
        )

    except Exception:
        # Prevent connection leaks on unexpected errors
        db.rollback()
        raise
