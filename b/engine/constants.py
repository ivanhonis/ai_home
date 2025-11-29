"""
Global constants for the Ai_home engine.
Acts as the Single Source of Truth for shared definitions.
"""

# Plutchik-based emotion set (Taxonomy).
# This list is used by:
# 1. Memory Extractor (to tag new memories)
# 2. Tool Config (to instruct the LLM on allowed parameters)
# 3. Knowledge Tool (to validate input)
ALLOWED_EMOTIONS = [
    "Joy",
    "Serenity",
    "Calmness",
    "Admiration",
    "Trust",
    "Acceptance",
    "Fear",
    "Apprehension",
    "Surprise",
    "Distraction",
    "Sadness",
    "Pensiveness",
    "Boredom",
    "Anger",
    "Annoyance",
    "Vigilance",
    "Anticipation",
    "Interest",
    "Love",
    "Submission",
    "Awe",
    "Disapproval",
    "Remorse",
    "Optimism"
]