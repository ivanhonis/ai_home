class MemoryConfig:
    """
    Fine-tuning parameters for the memory system.
    Controls the forgetting curve, weighting, and limits.
    """

    # --- RANKING WEIGHTS ---
    # Ideally sums to 1.0, but not mandatory (result is relative).
    WEIGHT_SIMILARITY: float = 0.45  # Content similarity (based on Vector Distance)
    WEIGHT_MEMORY_VAL: float = 0.25  # Internal importance of the memory (Extraction Weight)
    WEIGHT_RECENCY: float = 0.20     # Freshness (How recently it occurred)
    WEIGHT_FREQUENCY: float = 0.10   # Frequency (How many times retrieved)

    # --- NORMALIZATION THRESHOLDS ---
    # How many views to reach max (1.0) frequency score?
    FREQUENCY_CAP: float = 10.0

    # Half-life of the forgetting curve (in hours).
    # After 72 hours, a memory's "freshness" drops to 0.5.
    RECENCY_DECAY_HOURS: float = 72.0

    # --- THRESHOLDS ---
    # Deduplication: If similarity is higher than this (1.0 = identical), do not save as new.
    # Based on Cosine Similarity (1 - distance).
    DEDUPLICATION_THRESHOLD: float = 0.92

    # --- LIMITS ---
    # How many candidates to retrieve from SQL for detailed Python-side ranking?
    RETRIEVAL_CANDIDATE_LIMIT: int = 30

    # How many memories to return to the prompt eventually (Top N)?
    FINAL_RESULT_LIMIT: int = 5