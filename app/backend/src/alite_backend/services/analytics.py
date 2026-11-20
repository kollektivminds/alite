# app/backend/services/analytics.py
# Outline for Bayesian Knowledge Tracing (BKT) probability updates.

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

import alite_backend.db.schemas as schemas
from alite_backend.db.models import (
    KSA,
    EnumItemFormat,
    Exercise,
    Item,
    ItemResponse,
    ItemTarget,
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
    memory_strength: float, last_practiced: datetime
) -> float:
    """
    Calculates current memory retention probability using an exponential forgetting curve.
    R = exp(-delta_t / S)
    """  # noqa: E501
    now = datetime.now(timezone.utc)
    delta_days = (now - last_practiced).total_seconds() / 86400.0
    if delta_days < 0:
        delta_days = 0.0

    # avoid division by zero
    strength = max(0.01, memory_strength)
    retention = math.exp(-delta_days / strength)
    return retention


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
        )

        if is_correct:
            state.memory_strength = round(state.memory_strength + base_strength_gain, 4)
        else:
            state.memory_strength = max(0.25, round(state.memory_strength * 0.85, 4))

        state.last_practiced = now
        updated_states.append(state)

    return updated_states


def build_student_dashboard(
    db: Session,
    user_id: int,
    as_of: Optional[datetime] = None,
) -> schemas.StudentDashboardSummary:
    """
    Aggregates a learner's BKT mastery (p_known), time-decayed Ebbinghaus retention,
    and first-attempt accuracy across StudentKSAState and ItemResponse rows.
    """
    now = _to_utc(as_of, datetime.now(timezone.utc))

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

    # total logged attempts across all retry counts
    total_attempts = (
        db.scalar(
            select(func.count())
            .select_from(ItemResponse)
            .where(ItemResponse.user_id == user_id)  # type: ignore
        )
        or 0
    )

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

    # fetch KSA states joined with KSA metadata for readable labels.
    stmt = (
        select(StudentKSAState, KSA)
        .join(KSA, StudentKSAState.ksa_id == KSA.id)  # type: ignore
        .where(StudentKSAState.user_id == user_id)  # type: ignore
    )
    rows = db.execute(stmt).all()

    grouped_by_ksa: Dict[int, List[tuple[StudentKSAState, KSA]]] = defaultdict(list)
    for state, ksa in rows:
        if ksa.id is not None:
            grouped_by_ksa[ksa.id].append((state, ksa))

    ksa_items: List[schemas.StudentKSAMasteryItem] = []
    all_p_known: List[float] = []
    all_retentions: List[float] = []

    for ksa_id, entries in grouped_by_ksa.items():
        ksa_meta = entries[0][1]
        p_vals = [st.p_known for st, _ in entries]
        r_vals = [
            calculate_ebbinghaus_retention(
                memory_strength=st.memory_strength,
                last_practiced=_to_utc(st.last_practiced, now),
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

        ksa_items.append(
            schemas.StudentKSAMasteryItem(
                ksa_id=ksa_id,
                ksa_name=ksa_meta.name,
                parent_id=ksa_meta.parent_id,
                avg_p_known=round(avg_p, 4),
                avg_retention=round(avg_r, 4),
                tracked_targets=len(entries),
                last_practiced=latest_practiced,
            )
        )

    ksa_items.sort(key=lambda item: item.avg_p_known)

    return schemas.StudentDashboardSummary(
        user_id=user_id,
        total_attempts=total_attempts,
        first_attempt_accuracy=round(first_attempt_acc, 4),
        exercises_completed=exercises_completed,
        mean_p_known=round(sum(all_p_known) / len(all_p_known), 4)
        if all_p_known
        else 0.0,
        mean_retention=round(sum(all_retentions) / len(all_retentions), 4)
        if all_retentions
        else 0.0,
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
