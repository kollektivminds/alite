# alite_backend/api/trainer/exercises.py
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, List, Optional, Set, Tuple

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.services.exercise_router import ExerciseRouter
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, false, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()
HEX_HANDLE_PATTERN = re.compile(r"^[0-9a-fA-F]{8}$")


def reconcile_start_time(
    client_start: Optional[datetime], response_time_ms: int, server_now: datetime
) -> datetime:
    """
    Reconciles client-reported start time against server reality.
    Guarantees monotonically valid timestamps without negative durations.
    """
    # maximum tolerable discrepancy between client clock and server estimation (network latency allowance)
    CLOCK_SKEW_TOLERANCE_SECONDS = 10.0

    # monotonically expected start time based on reported reaction latency
    expected_start = server_now - timedelta(milliseconds=max(0, response_time_ms))

    if client_start is None:
        return expected_start

    # ensure timezone-aware comparison (UTC)
    if client_start.tzinfo is None:
        client_start = client_start.replace(tzinfo=timezone.utc)

    # check clock skew delta
    skew = abs((client_start - expected_start).total_seconds())

    # if client clock is within reasonable network/drift tolerance, respect client timestamp.
    # otherwise, fallback to server estimation to protect database telemetry.
    if skew <= CLOCK_SKEW_TOLERANCE_SECONDS and client_start <= server_now:
        return client_start

    return expected_start


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
        select(models.ItemOption.option_text)  # type: ignore
        .where(models.ItemOption.item_id == item_id)
        .where(models.ItemOption.is_correct.is_(True))  # type: ignore
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


def normalize_lexical_token(token: str) -> str:
    """Removes stress marks, leading/trailing whitespace, and canonicalizes casing."""
    decomposed = unicodedata.normalize("NFD", token.strip().lower())
    # Strip combining acute accents (U+0301) commonly used in Russian language pedagogy
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


def is_hex_handle_sequence(tokens: List[str]) -> bool:
    """
    Проверяет, является ли переданный список токенов последовательностью hex-хэндлов.
    Исключает ошибочное принятие обычных слов естественного языка за UUID-хэндлы.
    """
    if not tokens:
        return False
    return all(bool(HEX_HANDLE_PATTERN.fullmatch(t.strip())) for t in tokens)


def normalize_sentence_text(text: str, preserve_yo: bool = False) -> str:
    """
    Детерминированно нормализует предложение для синтаксической проверки порядка слов.

    Пайплайн нормализации:
    1. Сжатие всех пробельных символов в один пробел и обрезка краёв.
    2. NFD-декомпозиция и удаление диакритических знаков ударения (категория 'Mn').
    3. Приведение к нижнему регистру через casefold().
    4. Замена 'ё' на 'е' (если не включен строгий режим).
    5. Унификация всех видов тире к дефису '-'.
    6. Удаление кавычек (как прямых, так и «ёлочек»).
    7. Удаление финальных знаков препинания предложения (.?!).
    8. Рекомпозиция в каноническую форму NFC.
    """
    if not text:
        return ""

    # Сжатие пробелов
    cleaned = re.sub(r"\s+", " ", text.strip())

    # Снятие знаков ударения
    decomposed = unicodedata.normalize("NFD", cleaned)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    folded = stripped.casefold()

    if not preserve_yo:
        folded = folded.replace("ё", "е")

    # Унификация тире и удаление кавычек
    folded = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015]", "-", folded)
    folded = re.sub(r"[\u00AB\u00BB\u201C\u201D\u201E\u201F\"]", "", folded)

    # Удаление финальной точки/знака вопроса/восклицания на конце предложения
    folded = re.sub(r"[.?!]+$", "", folded).strip()

    return unicodedata.normalize("NFC", folded)


def evaluate_unscramble_response(
    db: Session,
    item: models.Item,
    submitted_answer: str,
) -> Tuple[bool, str, int, int]:
    """
    Оценивает ответ студента на задание типа 'unscramble'.

    Поддерживает два валидных входных формата:
    1. Список 8-значных hex-хэндлов (в виде JSON-массива, через запятую или пробел).
    2. Готовая текстовая строка собранного предложения.

    Возвращает:
        Tuple[is_correct, master_solution, matched_positions, total_tokens]
    """
    raw_submission = submitted_answer.strip()

    # 1. Извлечение эталонного предложения
    master_solution = ""
    if item.settings and isinstance(item.settings, dict):
        master_solution = item.settings.get("solution", "")

    if not master_solution:
        stmt = (
            select(models.ItemOption.option_text)
            .where(
                and_(
                    models.ItemOption.item_id == item.id,
                    models.ItemOption.explanation == "complete_sentence",
                )
            )
            .limit(1)
        )
        master_solution = db.scalar(stmt) or ""

    # 2. Извлечение эталонных позиций токенов с числовой сортировкой
    pos_stmt = select(models.ItemOption).where(
        and_(
            models.ItemOption.item_id == item.id,
            models.ItemOption.explanation.like("position:%"),
        )
    )
    ordered_option_records = list(db.scalars(pos_stmt).all())

    # Защита от лексикографической сортировки ('position:10' < 'position:2')
    def get_position_index(opt: models.ItemOption) -> int:
        if opt.explanation and ":" in opt.explanation:
            part = opt.explanation.split(":", 1)[1]
            if part.isdigit():
                return int(part)
        return 0

    ordered_option_records.sort(key=get_position_index)
    total_tokens = len(ordered_option_records)

    # Если в базе нет детальных записей позиций, создаем резерв из слов эталона
    if total_tokens == 0 and master_solution:
        total_tokens = len(master_solution.split())

    # -------------------------------------------------------------------------
    # ВЕТКА 1: Проверка последовательности opaque-хэндлов
    # -------------------------------------------------------------------------
    candidate_handles: List[str] = []

    if raw_submission.startswith("[") and raw_submission.endswith("]"):
        try:
            parsed = json.loads(raw_submission)
            if isinstance(parsed, list):
                candidate_handles = [str(h).strip() for h in parsed]
        except Exception:
            candidate_handles = []
    elif "," in raw_submission:
        candidate_handles = [h.strip() for h in raw_submission.split(",") if h.strip()]
    elif " " in raw_submission:
        candidate_handles = raw_submission.split()

    # Вход только если ВСЕ элементы строго соответствуют hex-шаблону хэндла
    if candidate_handles and is_hex_handle_sequence(candidate_handles):
        handle_to_expected_pos = {
            opt.option_uuid.hex[:8]: idx
            for idx, opt in enumerate(ordered_option_records)
        }

        matched_positions = 0
        for actual_pos, handle in enumerate(candidate_handles):
            if handle_to_expected_pos.get(handle) == actual_pos:
                matched_positions += 1

        is_correct = (matched_positions == total_tokens) and (
            len(candidate_handles) == total_tokens
        )
        return is_correct, master_solution, matched_positions, total_tokens

    # -------------------------------------------------------------------------
    # ВЕТКА 2: Проверка по тексту предложения (Surface Text Comparison)
    # -------------------------------------------------------------------------
    norm_sub = normalize_sentence_text(raw_submission)
    norm_sol = normalize_sentence_text(master_solution)

    # Точное совпадение нормализованных строк
    is_correct = bool(norm_sub and norm_sub == norm_sol)

    # Защитный уровень: сравнение без знаков препинания (если студент случайно убрал запятую)
    if not is_correct and norm_sub and norm_sol:
        alpha_sub = re.sub(r"[^\w\s]", "", norm_sub)
        alpha_sol = re.sub(r"[^\w\s]", "", norm_sol)
        if alpha_sub == alpha_sol:
            is_correct = True

    # Расчет пословного прогресса для диагностического фидбека
    sub_words = norm_sub.split()
    sol_words = norm_sol.split()
    matched_positions = sum(1 for w1, w2 in zip(sub_words, sol_words) if w1 == w2)
    display_total = max(total_tokens, len(sol_words))

    # Если всё предложение верное, гарантируем равенство счётчиков
    if is_correct:
        matched_positions = display_total

    return is_correct, master_solution, matched_positions, display_total


@router.post("/{exercise_id}/complete", status_code=status.HTTP_200_OK)
def complete_exercise_session(
    exercise_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> dict[str, Any]:
    """
    Finalizes an active exercise session by stamping finish_time.
    Calculates total session duration for institutional analytics.
    """
    exercise = db.get(models.Exercise, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise {exercise_id} not found.",
        )

    # Ensure students cannot alter another user's assessment session
    if exercise.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to exercise session.",
        )

    # Prevent overwriting finish_time if session was already completed
    if exercise.finish_time is None:
        exercise.finish_time = datetime.now(timezone.utc)
        db.add(exercise)
        db.commit()
        db.refresh(exercise)

    duration_seconds = (exercise.finish_time - exercise.start_time).total_seconds()

    return {
        "exercise_id": exercise.id,
        "start_time": exercise.start_time.isoformat(),
        "finish_time": exercise.finish_time.isoformat(),
        "duration_seconds": round(duration_seconds, 3),
    }


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
        item = db.get(models.Item, submission.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {submission.item_id} not found.",
            )

        server_now = datetime.now(timezone.utc)
        canonical_answer: Optional[str] = None
        feedback_message: Optional[str] = None
        is_correct = False

        # Monotonic start time reconciliation
        if item.start_time is None:
            item.start_time = reconcile_start_time(
                client_start=submission.client_item_start,
                response_time_ms=submission.response_time_ms,
                server_now=server_now,
            )
            db.add(item)

        # polymorphic format evaluation
        if item.item_format == models.EnumItemFormat.FLASHCARD:
            is_correct = submission.response.lower() in {"remembered", "mastered"}
            feedback_message = "Recall status updated."

        elif item.item_format == models.EnumItemFormat.UNSCRAMBLE:
            is_correct, canonical_answer, matched, total = evaluate_unscramble_response(
                db=db,
                item=item,
                submitted_answer=submission.response,
            )

            if is_correct:
                feedback_message = "Correct! You reconstructed the sentence perfectly."
            elif submission.is_final_attempt:
                feedback_message = (
                    "Incorrect word order. The correct sentence is shown below."
                )
            else:
                feedback_message = (
                    f"Not quite. {matched} of {total} words are in the correct position. "
                    f"Try rearranging the remaining words. (Attempt {submission.attempt_num})"
                )

        else:
            # Set-membership verification (MCQ, FITB)
            is_correct, canonical_answer = get_canonical_and_evaluation(
                db=db,
                item_id=submission.item_id,
                submitted_answer=submission.response,
            )

            if is_correct:
                feedback_message = "Correct!"
            elif submission.is_final_attempt:
                feedback_message = "Incorrect. The correct answer is shown below."
            else:
                feedback_message = (
                    f"Incorrect. Try again! (Attempt {submission.attempt_num})"
                )

        # protect canonical key on intermediate failures
        should_reveal = is_correct or submission.is_final_attempt

        if should_reveal and item.finish_time is None:
            item.finish_time = server_now
            db.add(item)

        # Log psychometric attempt telemetry
        db.add(
            models.ItemResponse(
                user_id=current_user.id,
                item_id=submission.item_id,
                response=submission.response.strip(),
                is_correct=is_correct,
                response_time_ms=submission.response_time_ms,
                attempt_num=submission.attempt_num,
            )
        )
        db.commit()

        return schemas.AnswerResult(
            is_correct=is_correct,
            correct_answer=canonical_answer if should_reveal else None,
            explanation=(
                item.settings.get("syntactic_focus")
                if should_reveal and item.settings
                else None
            ),
            feedback=feedback_message,
            attempt_num=submission.attempt_num,
        )

    except Exception:
        db.rollback()
        raise
