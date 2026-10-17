# alite_backend/api/trainer/lemmas.py
import logging
from typing import Any, List, Optional

from alite_backend.api import deps
from alite_backend.api.trainer.translit import is_latin_text, latin_to_cyrillic
from alite_backend.db import schemas
from alite_backend.db.crud.word_crud import crud_lemma
from alite_backend.db.db_session import SessionLocal
from alite_backend.db.models import (
    EnumLookupStatus,
    EnumPartOfSpeech,
    Lemma,
    LookupQueue,
    User,
)
from alite_backend.services.lookup_validator import (
    LemmaCapabilityReport,
    LemmaReadinessValidator,
)
from alite_backend.words.pipeline import load_words
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=schemas.LemmaDetailsReturn)
def create_lemma(lemma_in: schemas.LemmaCreate, db: Session = Depends(deps.get_db)):
    return crud_lemma.create(db=db, obj_in=lemma_in)


@router.get("/search", response_model=List[schemas.LemmaSearchResults])
def search_lemmas_api(
    q: str = Query(
        ..., alias="q", min_length=2, description="The lemma text (EN/RU) to search for"
    ),
    db: Session = Depends(deps.get_db),
) -> List[Lemma]:
    try:
        results = crud_lemma.search_lemmas_fuzzy(db, query_str=q)
        return results
    except Exception as exc:
        # output the complete stack trace directly to Docker container stdout
        logger.exception("Lemma search query failed for input '%s'", q)

        # bubble up the exact error detail during development so the frontend can inspect it
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database search error: {str(exc)}",
        ) from exc


@router.get("/{lemma_id}", response_model=schemas.LemmaDetailsReturn)
def read_lemma(lemma_id: int, db: Session = Depends(deps.get_db)):
    """Fetch a specific lemma by ID."""
    lemma = crud_lemma.get(db=db, id=lemma_id)
    if not lemma:
        raise HTTPException(status_code=404, detail="Lemma not found")
    return lemma


def _resolve_lemma_id(result: Any) -> Optional[int]:
    """
    Safely extracts the integer primary key from diverse return types.

    Protects against psycopg2 type adaptation failures by ensuring that
    neither Lemma ORM instances nor collections are passed directly
    into SQL parameter bindings.
    """
    if not result:
        return None

    # Handle sequence outputs (e.g. List[Lemma] or List[int])
    if isinstance(result, (list, tuple)):
        if len(result) == 0:
            return None
        result = result[0]

    # Handle Lemma ORM model instances by extracting the surrogate key
    if isinstance(result, Lemma) or hasattr(result, "id"):
        return getattr(result, "id", None)

    # Handle direct scalar integer returns
    if isinstance(result, int):
        return result

    return None


def execute_background_etl_pipeline(token: str, queue_id: int) -> None:
    """
    Asynchronous ETL worker executed off the primary request thread.

    Engineering Principles:
    - Transaction Isolation: Uses SessionLocal() directly so the background thread
      does not inherit an HTTP request session that may already be closed.
    - Idempotency & Fault Tolerance: If word ingestion fails, rolls back the
      failed DDL/DML and marks the LookupQueue entry as FAILED rather than hanging.
    - Type Safety: Guarantees that LookupQueue.target_id is populated strictly
      with an integer primary key, resolving the psycopg2 'can't adapt type' error.
    """
    logger.info(
        "Executing background ETL for token '%s' (Queue ID: %d)", token, queue_id
    )

    # 1. Acquire an isolated database session dedicated to this background worker
    with SessionLocal() as db:
        try:
            # 2. Invoke the lexicographical scraper/loader pipeline
            scrape_result = load_words(db=db, word_s=[token])

            # 3. Extract the integer primary key from the scraper result
            target_lemma_id = _resolve_lemma_id(scrape_result)

            # 4. Fallback: If scraper did not return the entity directly, query the DB
            if not target_lemma_id:
                fallback_lemma = db.scalars(
                    select(Lemma).where(
                        or_(
                            Lemma.lem_text.ilike(token),  # type: ignore
                            Lemma.lem_canon.ilike(token),  # type: ignore
                        )
                    )
                ).first()
                if fallback_lemma:
                    target_lemma_id = fallback_lemma.id

            # 5. Retrieve the queue record and update status
            job = db.get(LookupQueue, queue_id)
            if not job:
                logger.error("Queue job %d not found during ETL completion.", queue_id)
                return

            if target_lemma_id:
                # Crucial Fix: target_id receives an integer, not a Lemma instance
                job.target_id = target_lemma_id
                job.status = EnumLookupStatus.COMPLETED
                db.commit()
                logger.info(
                    "ETL succeeded for '%s': Lemma ID %d linked to Queue ID %d.",
                    token,
                    target_lemma_id,
                    queue_id,
                )
            else:
                # Scraper completed execution without raising, but no Lemma record was created
                job.status = EnumLookupStatus.FAILED
                db.commit()
                logger.warning(
                    "ETL finished for '%s' but no Lemma was persisted. Queue ID %d marked as FAILED.",
                    token,
                    queue_id,
                )

        except Exception as exc:
            db.rollback()
            logger.exception("Background ETL failed for token '%s': %s", token, exc)

            # Update queue status to FAILED in a clean transaction
            try:
                job = db.get(LookupQueue, queue_id)
                if job:
                    job.status = EnumLookupStatus.FAILED
                    db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to mark queue job %d as FAILED.", queue_id)


@router.post(
    "/pipeline-lookup",
    response_model=schemas.PipelineLookupResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_external_pipeline_lookup(
    payload: schemas.PipelineLookupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> schemas.PipelineLookupResponse:
    """
    Dispatches single or batch word tokens to the background extraction queue.
    """
    outcomes: List[schemas.PipelineItemOutcome] = []
    queued_count = 0

    # Ensure token list is uniformly extracted from request payload
    tokens = (
        payload.tokens if payload.tokens else ([payload.token] if payload.token else [])
    )

    # Check sliding-window user rate limiting
    remaining_attempts = 10
    reset_in_seconds = 0
    if hasattr(deps, "pipeline_rate_limiter"):
        try:
            remaining_attempts, reset_in_seconds = (
                deps.pipeline_rate_limiter.check_and_increment(current_user.id)  # type: ignore
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before submitting more requests.",
            )

    for raw_token in tokens:
        clean_token = raw_token.strip()  # type: ignore
        if not clean_token:
            continue

        # Transliterate Latin inputs into canonical Cyrillic before database matching
        canonical_token = (
            latin_to_cyrillic(clean_token)
            if is_latin_text(clean_token)
            else clean_token
        )

        # 1. Idempotency Check: Verify whether Lemma already exists
        lemma_stmt = select(Lemma).where(
            or_(
                Lemma.lem_text.ilike(canonical_token),  # type: ignore
                Lemma.lem_canon.ilike(canonical_token),  # type: ignore
            )
        )
        existing_lemma = db.scalars(lemma_stmt).first()

        if existing_lemma:
            outcomes.append(
                schemas.PipelineItemOutcome(
                    token=canonical_token,
                    status="already_exists",
                    existing_lemma_id=existing_lemma.id,
                    message=f"'{canonical_token}' already exists in dictionary.",
                )
            )
            continue

        # 2. Queue Deduplication: Check if token is actively PENDING or PROCESSING
        queue_stmt = select(LookupQueue).where(
            LookupQueue.target_lem == canonical_token,  # type: ignore
            func.lower(cast(LookupQueue.status, String)).in_(["pending", "processing"]),
        )
        active_job = db.scalars(queue_stmt).first()

        if active_job:
            outcomes.append(
                schemas.PipelineItemOutcome(
                    token=canonical_token,
                    status="in_progress",
                    queue_id=active_job.id,
                    message=f"'{canonical_token}' is currently being fetched.",
                )
            )
            continue

        # 3. Create persistent Queue Job
        new_job = LookupQueue(
            target_lem=canonical_token,
            requested_by=current_user.id,
            status=EnumLookupStatus.PENDING,
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # 4. Dispatch background task
        # Notice: Only primitive parameters (token, queue_id) are passed to add_task
        background_tasks.add_task(
            execute_background_etl_pipeline,
            token=canonical_token,
            queue_id=new_job.id,  # type: ignore
        )

        queued_count += 1
        outcomes.append(
            schemas.PipelineItemOutcome(
                token=canonical_token,
                status="queued",
                queue_id=new_job.id,
                message=f"'{canonical_token}' queued for web corpus extraction.",
            )
        )

    summary_message = (
        f"Queued {queued_count} word(s) successfully."
        if queued_count > 0
        else "No new words were queued."
    )

    return schemas.PipelineLookupResponse(
        results=outcomes,
        total_requested=len(tokens),
        total_queued=queued_count,
        remaining_attempts=remaining_attempts,
        reset_seconds=reset_in_seconds,
        token=(
            payload.token
            if isinstance(payload.token, str)
            else (tokens[0] if tokens else None)
        ),  # type: ignore
        status=outcomes[0].status if outcomes else "queued",
        message=summary_message,
    )


def evaluate_lemma_capabilities(
    db: Session, lemma_id: int
) -> schemas.LemmaReadinessItem:
    """
    Evaluates what pedagogical drills a lemma can support.

    Distinguishes between fatal errors (completely missing definitions or missing record)
    and non-blocking advisory gaps (partial inflection tables).
    """
    stmt = (
        select(Lemma)
        .where(Lemma.id == lemma_id)  # type: ignore
        .options(
            selectinload(Lemma.definitions),  # type: ignore
            selectinload(Lemma.pronunciations),  # type: ignore
            selectinload(Lemma.lemma_word_form),  # type: ignore
            selectinload(Lemma.related_to),  # type: ignore
        )  # type: ignore
    )
    lemma = db.scalars(stmt).first()

    if not lemma:
        return schemas.LemmaReadinessItem(
            lemma_id=lemma_id,
            lem_text="UNKNOWN",
            is_usable=False,
            supported_item_types=[],
            advisory_warnings=[],
            critical_errors=["Lemma record does not exist in the database."],
        )

    critical_errors: List[str] = []
    advisory_warnings: List[str] = []
    supported_types: List[str] = []

    # 1. Base semantic verification (Required for almost all exercise types)
    if not lemma.definitions:
        critical_errors.append("No definitions recorded.")
    else:
        supported_types.extend(["lem_to_def", "def_to_lem"])

    # 2. Phonetic support
    if lemma.pronunciations:
        supported_types.extend(["lem_to_pron", "pron_to_lem"])

    # 3. Part-of-speech classification support
    if lemma.pos:
        supported_types.extend(["lem_to_pos", "pos_to_lem"])

    # 4. Grammatical & Inflectional Analysis (Non-blocking advisories)
    form_count = len(lemma.lemma_word_form) if lemma.lemma_word_form else 0

    if lemma.pos == EnumPartOfSpeech.VERB:
        if lemma.verb_aspect:
            supported_types.append("verb_to_aspt")
        else:
            advisory_warnings.append("Missing verb aspect (imperfective/perfective).")

        if form_count > 0:
            supported_types.append("verb_to_conj_form")
        else:
            advisory_warnings.append("No conjugated forms recorded.")

    elif lemma.pos == EnumPartOfSpeech.NOUN:
        if lemma.noun_gender:
            supported_types.append("noun_to_gend")
        else:
            advisory_warnings.append("Missing grammatical gender.")

        if form_count > 0:
            supported_types.append("noun_form_to_gram")
        else:
            advisory_warnings.append("No declined case forms recorded.")

    # A lemma is pedagogically usable if it has at least one valid drill capability
    # and no fatal structural omissions.
    is_usable = (len(critical_errors) == 0) and (len(supported_types) > 0)

    return schemas.LemmaReadinessItem(
        lemma_id=lemma.id,  # type: ignore
        lem_text=lemma.lem_canon or lemma.lem_text,
        is_usable=is_usable,
        supported_item_types=supported_types,
        advisory_warnings=advisory_warnings,
        critical_errors=critical_errors,
    )


@router.post(
    "/validate-exercise-pool",
    response_model=schemas.PoolValidationResponse,
    status_code=status.HTTP_200_OK,
)
def validate_exercise_pool(
    payload: schemas.PoolValidationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> schemas.PoolValidationResponse:
    """
    Evaluates readiness of staged vocabulary against pedagogical minimums.

    Allows exercises to start as long as the quorum threshold of eligible words is satisfied.
    """
    reports: List[schemas.LemmaReadinessItem] = []
    eligible_ids: List[int] = []
    unusable_ids: List[int] = []

    for l_id in payload.lemma_ids:
        report = evaluate_lemma_capabilities(db, l_id)
        reports.append(report)
        if report.is_usable:
            eligible_ids.append(l_id)
        else:
            unusable_ids.append(l_id)

    # Quorum verification: proceed if eligible items meet or exceed min_required_words
    can_start = len(eligible_ids) >= payload.min_required_words

    if can_start:
        if len(unusable_ids) > 0:
            summary = (
                f"{len(eligible_ids)} of {len(payload.lemma_ids)} words ready. "
                f"{len(unusable_ids)} words omitted due to incomplete data."
            )
        else:
            summary = f"All {len(eligible_ids)} words ready for exercise generation."
    else:
        summary = (
            f"Insufficient usable words. Found {len(eligible_ids)} eligible lemmas; "
            f"minimum required is {payload.min_required_words}."
        )

    return schemas.PoolValidationResponse(
        can_start=can_start,
        total_requested=len(payload.lemma_ids),
        eligible_count=len(eligible_ids),
        eligible_lemma_ids=eligible_ids,
        unusable_lemma_ids=unusable_ids,
        reports=reports,
        summary_message=summary,
    )


@router.post(
    "/queue-status",
    response_model=List[schemas.PipelineItemOutcome],
    status_code=status.HTTP_200_OK,
)
def get_pipeline_queue_status(
    payload: schemas.PipelineStatusRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> List[schemas.PipelineItemOutcome]:
    """
    Polls the latest queue status for active in-session word lookups.
    Returns status: 'pending', 'processing', 'completed', or 'failed'.
    """
    outcomes: List[schemas.PipelineItemOutcome] = []
    if not payload.tokens:
        return outcomes

    for token in payload.tokens:
        clean_token = token.strip()
        if not clean_token:
            continue

        # Fetch the most recent queue record for this token
        queue_stmt = (
            select(LookupQueue)
            .where(LookupQueue.target_lem == clean_token)  # type: ignore
            .order_by(LookupQueue.id.desc())  # type: ignore
        )
        job = db.scalars(queue_stmt).first()

        if job:
            status_val = (
                job.status.value if hasattr(job.status, "value") else str(job.status)
            )
            status_clean = status_val.lower()

            if status_clean == "completed":
                msg = f"'{clean_token}' successfully parsed and added to dictionary."
            elif status_clean == "failed":
                msg = f"Extraction failed for '{clean_token}'. Check external dictionary corpus."
            elif status_clean in ("pending", "processing"):
                msg = f"'{clean_token}' is currently being fetched."
            else:
                msg = f"Status: {status_clean}"

            outcomes.append(
                schemas.PipelineItemOutcome(
                    token=clean_token,
                    status=status_clean,
                    queue_id=job.id,
                    existing_lemma_id=job.target_id,
                    message=msg,
                )
            )
        else:
            # Fallback: Check if lemma already exists directly in the dictionary
            lemma_stmt = select(Lemma).where(
                or_(
                    Lemma.lem_text.ilike(clean_token),  # type: ignore
                    Lemma.lem_canon.ilike(clean_token),  # type: ignore
                )
            )
            lemma = db.scalars(lemma_stmt).first()
            if lemma:
                outcomes.append(
                    schemas.PipelineItemOutcome(
                        token=clean_token,
                        status="completed",
                        existing_lemma_id=lemma.id,
                        message=f"'{clean_token}' exists in dictionary.",
                    )
                )
            else:
                outcomes.append(
                    schemas.PipelineItemOutcome(
                        token=clean_token,
                        status="failed",
                        message=f"No record found for '{clean_token}'.",
                    )
                )

    return outcomes
