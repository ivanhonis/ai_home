from datetime import datetime, timezone
from .config import MemoryConfig


def calculate_recency_score(created_at: datetime) -> float:
    """
    Calculates the Recency score based on an exponential decay curve.

    Formula: 1 / (1 + (elapsed_hours / decay_half_life))
    - If happened now: 1.0
    - If happened 'RECENCY_DECAY_HOURS' ago: 0.5
    - If very old: approaches 0.0
    """
    if created_at is None:
        return 0.0

    # Ensure timezones are correct (UTC)
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        # If timezone info is missing, assume UTC
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_seconds = (now - created_at).total_seconds()
    age_hours = age_seconds / 3600.0

    # Protection against future dates (should not happen)
    if age_hours < 0:
        age_hours = 0

    return 1.0 / (1.0 + (age_hours / MemoryConfig.RECENCY_DECAY_HOURS))


def calculate_frequency_score(access_count: int) -> float:
    """
    Normalizes access Frequency between 0.0 and 1.0.

    Logic: Linear growth until 'FREQUENCY_CAP' is reached.
    If access_count >= FREQUENCY_CAP, then score is 1.0 (saturation).
    """
    if access_count is None or access_count < 0:
        return 0.0

    score = float(access_count) / MemoryConfig.FREQUENCY_CAP
    return min(score, 1.0)


def calculate_final_score(
        sim_score: float,
        internal_weight: float,
        recency_score: float,
        freq_score: float,
        has_emotional_overlap: bool = False
) -> float:
    """
    Calculates the final Relevance Score based on the weights.
    """
    base_score = (
            (sim_score * MemoryConfig.WEIGHT_SIMILARITY) +
            (internal_weight * MemoryConfig.WEIGHT_MEMORY_VAL) +
            (recency_score * MemoryConfig.WEIGHT_RECENCY) +
            (freq_score * MemoryConfig.WEIGHT_FREQUENCY)
    )

    # Add emotional bonus (if there is a common emotion with the current state)
    # This is a small nudge (e.g., +5%) to help empathic matches
    if has_emotional_overlap:
        base_score += 0.05

    return base_score