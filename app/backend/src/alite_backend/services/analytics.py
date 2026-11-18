# app/backend/services/analytics.py
# Outline for Bayesian Knowledge Tracing (BKT) probability updates.

import math
from datetime import datetime, timezone


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

    # Avoid division by zero
    strength = max(0.01, memory_strength)
    retention = math.exp(-delta_days / strength)
    return retention
