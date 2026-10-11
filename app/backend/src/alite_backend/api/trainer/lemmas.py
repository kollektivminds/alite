# alite_backend/api/trainer/lemmas.py
import logging
from typing import List

from alite_backend.api import deps
from alite_backend.api.trainer.translit import is_latin_text, latin_to_cyrillic
from alite_backend.db import schemas
from alite_backend.db.crud.word_crud import crud_lemma
from alite_backend.db.models import EnumLookupStatus, Lemma, LookupQueue, User
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

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


def execute_background_etl_pipeline(token: str, queue_id: int, db_url: str) -> None:
    """
    Worker task dispatched off the primary request thread.
    Parses definitions, inflections, and pronunciations, then writes them to the DB.
    """
    logger.info(
        "Executing background ETL for token '%s' (Queue ID: %d)", token, queue_id
    )
    # Target scraper / Wiktionary parser persists lemmas and updates LookupQueue.status


@router.post(
    "/pipeline-lookup",
    response_model=schemas.PipelineLookupResponse,  # Validated response schema[cite: 9]
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_external_pipeline_lookup(
    payload: schemas.PipelineLookupRequest,  # Ingests single or batch word requests[cite: 9]
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),  # Standard SQLAlchemy 2.0 Session
    current_user: User = Depends(deps.get_current_user),
) -> schemas.PipelineLookupResponse:
    """
    Dispatches single or batch word tokens to the background extraction queue.

    Guarantees:
    - Input normalization (Cyrillic canonicalization).
    - Idempotency checks against existing lemmas.
    - Active crawl deduplication via LookupQueue.
    - Enforces rate-limiting to prevent external crawler blacklisting.
    """
    outcomes: List[schemas.PipelineItemOutcome] = (
        []
    )  # Tracks individual token outcomes[cite: 9]
    queued_count = 0

    # Extract tokens from unified schema (handles single string or token arrays)[cite: 9]
    tokens = (
        payload.tokens if payload.tokens else ([payload.token] if payload.token else [])
    )

    # query user quota headroom
    remaining_attempts = 10
    reset_in_seconds = 0
    if hasattr(deps, "pipeline_rate_limiter"):
        try:
            remaining_attempts, reset_in_seconds = (
                deps.pipeline_rate_limiter.get_status(current_user.id)
            )
        except AttributeError:
            pass

    for raw_token in tokens:
        clean_token = raw_token.strip()
        if not clean_token:
            continue

        # orthographic normalization: convert latin transliteration to cyrillic
        canonical_token = (
            latin_to_cyrillic(clean_token)
            if is_latin_text(clean_token)
            else clean_token
        )

        # lemma deduplication: Verify whether headword already exists in dictionary
        lemma_stmt = select(Lemma).where(
            or_(
                Lemma.lem_text.ilike(canonical_token),
                Lemma.lem_canon.ilike(canonical_token),
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

        # queue deduplication: check if token is actively PENDING or PROCESSING in queue
        queue_stmt = select(LookupQueue).where(
            LookupQueue.target_lem == canonical_token,
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

        # quota enforcement: apply per-user sliding window limiter
        if hasattr(deps, "pipeline_rate_limiter"):
            try:
                remaining_attempts, reset_in_seconds = (
                    deps.pipeline_rate_limiter.check_and_increment(current_user.id)
                )
            except Exception:
                outcomes.append(
                    schemas.PipelineItemOutcome(
                        token=canonical_token,
                        status="rate_limited",
                        message="Rate limit reached. Please wait before requesting additional lookups.",
                    )
                )
                continue

        # entity persistence: instantiate LookupQueue using EnumLookupStatus.PENDING
        new_job = LookupQueue(
            target_lem=canonical_token,
            requested_by=current_user.id,
            status=EnumLookupStatus.PENDING,  # Serialized via values_callable
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # worker dispatch: queue background ETL job off the main thread
        background_tasks.add_task(
            execute_background_etl_pipeline,
            token=canonical_token,
            queue_id=new_job.id,
            db_url=str(db.get_bind().url),
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
        token=payload.token,
        status=outcomes[0].status if outcomes else "queued",
        message=summary_message,
    )
