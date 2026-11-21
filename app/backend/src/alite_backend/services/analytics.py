# app/backend/services/analytics.py
# Outline for Bayesian Knowledge Tracing (BKT) probability updates.

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

import alite_backend.db.schemas as schemas
from alite_backend.db.models import (
    KSA,
    EnumItemFormat,
    EnumKSAStatusBand,
    Exercise,
    Item,
    ItemResponse,
    ItemTarget,
    LemmaInLessonList,
    LessonListInModule,
    StudentKSAState,
    UserGroup,
    UserInGroup,
)

logger = logging.getLogger(__name__)


def _to_utc(dt: Optional[datetime], fallback: datetime) -> datetime:
    """Ensures a datetime is timezone-aware in UTC for safe arithmetic."""
    if dt is None:
        return fallback
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def update_bkt_probability(
    p_known: float,
    is_correct: bool,
    slip: float = 0.1,
    guess: float = 0.2,
    transit: float = 0.1,
) -> float:
    """
    Updates the probability of mastery P(L_n) given a student's response
    using standard Bayesian Knowledge Tracing equations.

    Args:
        p_known: Current probability that the student knows the skill.
        is_correct: Boolean representing whether the attempt was correct.
        slip: Probability that a student who knows the skill answers incorrectly.
        guess: Probability that a student who does not know the skill guesses correctly.
        transit: Probability that a student transitions from unknown to known state.
    """
    if is_correct:
        # P(L | correct)
        p_l_given_obs = (p_known * (1.0 - slip)) / (
            p_known * (1.0 - slip) + (1.0 - p_known) * guess
        )
    else:
        # P(L | incorrect)
        p_l_given_obs = (p_known * slip) / (
            p_known * slip + (1.0 - p_known) * (1.0 - guess)
        )

    # P(L_n+1) incorporating transition probability
    p_next_known = p_l_given_obs + (1.0 - p_l_given_obs) * transit
    return max(0.0, min(1.0, p_next_known))


def calculate_ebbinghaus_retention(
    memory_strength: float,
    last_practiced: datetime,
    as_of: Optional[datetime] = None,
) -> float:
    """
    Computes R = exp(-delta_t / S) using UTC-aware timestamps.
    Accepting `as_of` ensures dashboard snapshots evaluate decay at a single reference time.
    """
    now = _to_utc(as_of, datetime.now(timezone.utc))
    last = _to_utc(last_practiced, now)
    delta_days = max(0.0, (now - last).total_seconds() / 86400.0)
    strength = max(0.01, memory_strength)
    return math.exp(-delta_days / strength)


def apply_response_to_student_ksa_states(
    db: Session,
    user_id: int,
    item_id: int,
    is_correct: bool,
    attempt_num: int,
    observed_at: Optional[datetime] = None,
    base_strength_gain: float = 1.0,
) -> List[StudentKSAState]:
    """
    Updates or cold-starts StudentKSAState records for all KSA targets linked to `item_id`.

    Gating rules:
    - Ignores non-empirical FLASHCARD self-reports.
    - Only updates mastery on attempt_num == 1 (avoids retry / local-dependence bias).
    - Skips if an attempt_num == 1 response already exists for (user_id, item_id)
      or if an earlier attempt was already logged out of order.
    """  # noqa: E501
    now = _to_utc(observed_at, datetime.now(timezone.utc))

    # only initial attempts drive BKT and spacing-strength updates.
    if attempt_num != 1:
        return []

    item = db.get(Item, item_id)
    if item is None:
        return []

    # exclude self-reported flashcard check-ins from empirical mastery tracking.
    if item.item_format == EnumItemFormat.FLASHCARD:
        return []

    # guard against duplicate attempt_num == 1 submissions or out-of-order retries.  # noqa: E501
    prior_responses = list(
        db.scalars(
            select(ItemResponse).where(
                and_(
                    ItemResponse.user_id == user_id,  # type: ignore
                    ItemResponse.item_id == item_id,  # type: ignore
                )
            )
        ).all()
    )
    if any(r.attempt_num <= 1 for r in prior_responses):
        return []

    # fetch all ksa targets mapped to this item (supports multi-ksa q-matrix rows).
    targets = list(
        db.scalars(select(ItemTarget).where(ItemTarget.item_id == item_id)).all()  # type: ignore
    )
    if not targets:
        return []

    updated_states: List[StudentKSAState] = []

    for target in targets:
        # match nullable lemma_id safely with .is_() when lemma_id is none.
        lemma_clause = (
            StudentKSAState.lemma_id.is_(None)  # type: ignore
            if target.lemma_id is None
            else StudentKSAState.lemma_id == target.lemma_id
        )

        state = db.scalars(
            select(StudentKSAState).where(
                and_(
                    StudentKSAState.user_id == user_id,  # type: ignore
                    lemma_clause,  # type: ignore
                    StudentKSAState.ksa_id == target.ksa_id,  # type: ignore
                )
            )
        ).first()

        # cold-start state if this is the learner's first tracked exposure to this target.  # noqa: e501
        if state is None:
            state = StudentKSAState(
                user_id=user_id,
                lemma_id=target.lemma_id,
                ksa_id=target.ksa_id,
                p_known=0.1,
                memory_strength=1.0,
                last_practiced=now,
            )
            db.add(state)
            db.flush()

        # update bkt probability P(L_n).
        state.p_known = update_bkt_probability(
            p_known=state.p_known,
            is_correct=is_correct,
        )

        # evaluate prior retention before advancing last_practiced, then update strength.  # noqa: E501
        prior_last_practiced = _to_utc(state.last_practiced, now)
        _ = calculate_ebbinghaus_retention(
            memory_strength=state.memory_strength,
            last_practiced=prior_last_practiced,
            as_of=now,
        )

        if is_correct:
            state.memory_strength = round(state.memory_strength + base_strength_gain, 4)
        else:
            state.memory_strength = max(0.25, round(state.memory_strength * 0.85, 4))

        state.last_practiced = now
        updated_states.append(state)

    return updated_states


def _classify_ksa_band(
    p_known: float,
    retention: float,
    review_cutoff: float = 0.80,
) -> EnumKSAStatusBand:
    """Maps BKT mastery and Ebbinghaus retention to a learner-facing status band[cite: 23]."""
    if retention < review_cutoff and p_known >= 0.35:
        return EnumKSAStatusBand.NEEDS_REVIEW
    if p_known < 0.30:
        return EnumKSAStatusBand.FOUNDATIONAL_GAP
    if p_known <= 0.70:
        return EnumKSAStatusBand.ZPD_FOCUS
    return EnumKSAStatusBand.STRONG


def build_enriched_student_summary(
    db: Session,
    user_id: int,
    as_of: Optional[datetime] = None,
    review_retention_threshold: float = 0.80,
) -> Dict[str, object]:
    """
    Extends the base /analytics/student/me aggregation with ZPD focus suggestions,
    retention-risk flags, and parent-domain rollups for the student dashboard.
    """
    now = _to_utc(as_of, datetime.now(timezone.utc))

    # Query StudentKSAState joined with KSA so we have both leaf metadata and parent_id.
    stmt = (
        select(StudentKSAState, KSA)
        .join(KSA, StudentKSAState.ksa_id == KSA.id)  # type: ignore
        .where(StudentKSAState.user_id == user_id)  # type: ignore
    )
    rows = db.execute(stmt).all()

    # Optional lookup of parent KSA names to label domain rollups cleanly.
    all_ksas = {k.id: k for k in db.scalars(select(KSA)).all() if k.id is not None}

    grouped_by_ksa: Dict[int, List[tuple[StudentKSAState, KSA]]] = defaultdict(list)
    for state, ksa in rows:
        if ksa.id is not None:
            grouped_by_ksa[ksa.id].append((state, ksa))

    ksa_breakdown: List[Dict[str, object]] = []
    domain_accum: Dict[Optional[int], List[float]] = defaultdict(list)

    for ksa_id, entries in grouped_by_ksa.items():
        ksa_meta = entries[0][1]
        p_vals = [st.p_known for st, _ in entries]
        r_vals = [
            calculate_ebbinghaus_retention(
                memory_strength=st.memory_strength,
                last_practiced=_to_utc(st.last_practiced, now),
                as_of=now,
            )
            for st, _ in entries
        ]
        latest_practiced = max(
            (_to_utc(st.last_practiced, now) for st, _ in entries),
            default=None,
        )

        avg_p = round(sum(p_vals) / len(p_vals), 4)
        avg_r = round(sum(r_vals) / len(r_vals), 4)
        domain_accum[ksa_meta.parent_id].append(avg_p)

        ksa_breakdown.append(
            {
                "ksa_id": ksa_id,
                "ksa_name": ksa_meta.name,
                "parent_id": ksa_meta.parent_id,
                "avg_p_known": avg_p,
                "avg_retention": avg_r,
                "tracked_targets": len(entries),
                "last_practiced": latest_practiced.isoformat()
                if latest_practiced
                else None,
                "status_band": _classify_ksa_band(
                    avg_p, avg_r, review_retention_threshold
                ),
                "is_due_for_review": avg_r < review_retention_threshold,
            }
        )

    # Sort ascending by mastery so immediate bottlenecks appear first.
    ksa_breakdown.sort(key=lambda item: float(item["avg_p_known"]))  # type: ignore

    # Prioritize skills in the ZPD (0.30–0.70) first, then lowest mastery overall.
    zpd_candidates = [k for k in ksa_breakdown if k["status_band"] == "zpd_focus"]
    low_candidates = [k for k in ksa_breakdown if k["status_band"] != "zpd_focus"]
    recommended_focus = (zpd_candidates + low_candidates)[:3]

    domain_rollups = [
        {
            "parent_id": parent_id,
            "domain_name": all_ksas[parent_id].name
            if parent_id in all_ksas
            else "General",
            "avg_p_known": round(sum(vals) / len(vals), 4),
            "ksa_count": len(vals),
        }
        for parent_id, vals in domain_accum.items()
    ]

    return {
        "ksa_breakdown": ksa_breakdown,
        "recommended_focus": recommended_focus,
        "domain_rollups": domain_rollups,
    }


def _is_state_in_scope(
    state: StudentKSAState,
    scoped_lemma_ids: Optional[set[int]],
    include_non_lemma_states: bool,
) -> bool:
    """
    Determines whether a StudentKSAState row matches the active module/lesson filter.
    - When `scoped_lemma_ids is None`, all states for the user are included.
    - When a scope is active, lemma-backed states match if `state.lemma_id in scoped_lemma_ids`.
    - Nullable `lemma_id` states are included only when `include_non_lemma_states` is True.
    """
    if scoped_lemma_ids is None:
        return True
    if state.lemma_id is None:
        return include_non_lemma_states
    return state.lemma_id in scoped_lemma_ids


def _resolve_scoped_lemma_ids(
    db: Session,
    module_id: Optional[int] = None,
    lesson_id: Optional[int] = None,
) -> Optional[Set[int]]:
    """
    Resolves target Lemma IDs for an optional Module and/or LessonList.
    Returns `None` when neither filter is set (meaning all lemmas are in scope),
    or a `set[int]` (possibly empty) when a curriculum filter is active.
    """
    if module_id is None and lesson_id is None:
        return None

    # Build a SQLAlchemy 2.0 select over LemmaInLessonList joined with LessonListInModule
    # when module_id is provided so both module-wide and single-lesson scopes use one path.
    stmt = select(LemmaInLessonList.lem_id).join(  # type: ignore
        LessonListInModule,
        LemmaInLessonList.less_list_id == LessonListInModule.less_list_id,  # type: ignore[arg-type]
    )

    if module_id is not None:
        stmt = stmt.where(LessonListInModule.mod_id == module_id)  # type: ignore[arg-type]
    if lesson_id is not None:
        stmt = stmt.where(LemmaInLessonList.less_list_id == lesson_id)  # type: ignore[arg-type]

    return {lem_id for lem_id in db.scalars(stmt).all() if lem_id is not None}


def build_student_dashboard(
    db: Session,
    user_id: int,
    module_id: Optional[int] = None,
    lesson_id: Optional[int] = None,
    include_non_lemma_states: bool = False,
    as_of: Optional[datetime] = None,
    review_retention_threshold: float = 0.80,
) -> schemas.StudentDashboardSummary:
    """
    Builds the complete student analytics summary:
    - First-attempt empirical accuracy vs. total/retry attempt volume.
    - Per-KSA BKT mastery and time-decayed retention, sorted lowest-mastery first.
    - ZPD-prioritized focus recommendations and parent-domain rollups.
    """
    now = _to_utc(as_of, datetime.now(timezone.utc))

    scoped_lemma_ids = _resolve_scoped_lemma_ids(
        db=db,
        module_id=module_id,
        lesson_id=lesson_id,
    )

    # fetch first-attempt responses (attempt_num == 1) for empirical accuracy.
    first_attempts = list(
        db.scalars(
            select(ItemResponse).where(
                ItemResponse.user_id == user_id,  # type: ignore
                ItemResponse.attempt_num == 1,  # type: ignore
            )
        ).all()
    )
    total_first = len(first_attempts)
    correct_first = sum(1 for r in first_attempts if r.is_correct)
    first_attempt_acc = (correct_first / total_first) if total_first > 0 else 0.0

    # logged attempts across all retry counts
    total_attempts = (
        db.scalar(
            select(func.count())
            .select_from(ItemResponse)
            .where(ItemResponse.user_id == user_id)  # type: ignore
        )
        or 0
    )
    retry_attempts = max(0, total_attempts - total_first)

    # total exercises completed
    exercises_completed = (
        db.scalar(
            select(func.count())
            .select_from(Exercise)
            .where(
                Exercise.user_id == user_id,  # type: ignore
                Exercise.finish_time.isnot(None),  # type: ignore
            )
        )
        or 0
    )

    all_ksas = {
        k.id: k
        for k in db.scalars(select(KSA)).all()  # type: ignore
        if k.id is not None
    }

    # fetch KSA states joined with KSA metadata for readable labels.
    stmt = (
        select(StudentKSAState, KSA)
        .join(KSA, StudentKSAState.ksa_id == KSA.id)  # type: ignore
        .where(StudentKSAState.user_id == user_id)  # type: ignore
    )

    raw_rows: List[Tuple[StudentKSAState, KSA]] = list(db.execute(stmt).all())
    scoped_rows = [
        (state, ksa)
        for state, ksa in raw_rows
        if _is_state_in_scope(state, scoped_lemma_ids, include_non_lemma_states)
    ]

    grouped_by_ksa: Dict[int, List[Tuple[StudentKSAState, KSA]]] = defaultdict(list)
    for state, ksa in scoped_rows:
        if ksa.id is not None:
            grouped_by_ksa[ksa.id].append((state, ksa))

    ksa_items: List[schemas.StudentKSAMasteryItem] = []
    domain_p_accum: Dict[Optional[int], List[float]] = defaultdict(list)
    domain_r_accum: Dict[Optional[int], List[float]] = defaultdict(list)
    all_p_known: List[float] = []
    all_retentions: List[float] = []

    for ksa_id, entries in grouped_by_ksa.items():
        ksa_meta = entries[0][1]
        p_vals = [st.p_known for st, _ in entries]
        r_vals = [
            calculate_ebbinghaus_retention(
                memory_strength=st.memory_strength,
                last_practiced=_to_utc(st.last_practiced, now),
                as_of=now,
            )
            for st, _ in entries
        ]
        latest_practiced = max(
            (_to_utc(st.last_practiced, now) for st, _ in entries),
            default=None,
        )

        avg_p = sum(p_vals) / len(p_vals)
        avg_r = sum(r_vals) / len(r_vals)
        all_p_known.extend(p_vals)
        all_retentions.extend(r_vals)
        domain_p_accum[ksa_meta.parent_id].append(avg_p)
        domain_r_accum[ksa_meta.parent_id].append(avg_r)

        ksa_items.append(
            schemas.StudentKSAMasteryItem(
                ksa_id=ksa_id,
                ksa_name=ksa_meta.name,
                parent_id=ksa_meta.parent_id,
                avg_p_known=round(avg_p, 4),
                avg_retention=round(avg_r, 4),
                tracked_targets=len(entries),
                last_practiced=latest_practiced,
                status_band=_classify_ksa_band(
                    avg_p, avg_r, review_retention_threshold
                ),
                is_due_for_review=avg_r < review_retention_threshold,
            )
        )

    # sort ascending by mastery so immediate gaps surface first
    ksa_items.sort(key=lambda item: item.avg_p_known)

    # prioritize zpd skills first, then remaining lowest-mastery skills (up to 3)
    zpd_items = [
        k for k in ksa_items if k.status_band == schemas.EnumKSAStatusBand.ZPD_FOCUS
    ]
    other_items = [
        k for k in ksa_items if k.status_band != schemas.EnumKSAStatusBand.ZPD_FOCUS
    ]
    recommended_focus = (zpd_items + other_items)[:3]

    domain_rollups = [
        schemas.StudentDomainRollup(
            parent_id=parent_id,
            domain_name=all_ksas[parent_id].name
            if parent_id in all_ksas
            else "General",
            avg_p_known=round(sum(p_list) / len(p_list), 4),
            avg_retention=round(
                sum(domain_r_accum[parent_id]) / len(domain_r_accum[parent_id]), 4
            ),
            ksa_count=len(p_list),
        )
        for parent_id, p_list in domain_p_accum.items()
    ]

    return schemas.StudentDashboardSummary(
        user_id=user_id,
        total_attempts=total_attempts,
        retry_attempts=retry_attempts,
        first_attempt_accuracy=round(first_attempt_acc, 4),
        exercises_completed=exercises_completed,
        mean_p_known=round(sum(all_p_known) / len(all_p_known), 4)
        if all_p_known
        else 0.0,
        mean_retention=round(sum(all_retentions) / len(all_retentions), 4)
        if all_retentions
        else 0.0,
        recommended_focus=recommended_focus,
        domain_rollups=domain_rollups,
        ksa_breakdown=ksa_items,
    )


def build_class_analytics(
    db: Session,
    group_id: int,
    mastery_threshold: float = 0.6,
    as_of: Optional[datetime] = None,
) -> Optional[schemas.ClassAnalyticsSummary]:
    """
    Aggregates StudentKSAState across members of a UserGroup for instructor triage.
    Returns None if `group_id` does not exist.
    """
    group = db.get(UserGroup, group_id)
    if not group:
        return None

    now = _to_utc(as_of, datetime.now(timezone.utc))  # noqa: F841

    member_ids = list(
        db.scalars(
            select(UserInGroup.user_id).where(  # type: ignore
                UserInGroup.group_id == group_id
            )  # type: ignore
        ).all()
    )
    if not member_ids:
        return schemas.ClassAnalyticsSummary(
            group_id=group_id,
            group_name=group.group_name,
            student_count=0,
            cohort_mean_p_known=0.0,
            weakest_ksas=[],
            students=[],
        )

    # Compute per-student and per-KSA rollups across enrolled group members.
    # ... query StudentKSAState + User + KSA where user_id.in_(member_ids) ...
    raise NotImplementedError("Complete cohort rollup query using member_ids")


def build_admin_platform_summary(db: Session) -> schemas.AdminPlatformSummary:
    """
    Computes system-wide engagement, psychometric seeding coverage, and KSA health
    for administrative oversight.
    """
    # ... aggregate counts from User, Exercise, Item, ItemResponse, ItemIRT, KSA ...
    raise NotImplementedError("Complete admin platform summary query")
