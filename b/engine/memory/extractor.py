import logging
import json
from typing import Optional

# Importing shared LLM caller and data model
from engine.llm import call_llm
from .models import ExtractionResult

# Import Single Source of Truth for emotions
from engine.constants import ALLOWED_EMOTIONS

logger = logging.getLogger(__name__)


def extract_memory_from_context(context_text: str) -> Optional[ExtractionResult]:
    """
    Calls the LLM to analyze the provided text context and extract
    structured memory (Essence, Emotions, Weight, Lesson).

    Args:
        context_text: The last X elements of the conversation concatenated as a string.
                      (Expected format: 'Helper: ... \n Me: ...')

    Returns:
        ExtractionResult object or None in case of error.
    """
    if not context_text or not context_text.strip():
        logger.debug("Context text is empty, skipping extraction.")
        return None

    # Convert list to string for the prompt
    emotions_list_str = ", ".join(ALLOWED_EMOTIONS)

    # UPDATED: Added TERMINOLOGY RULES to prevent 'User' usage in database records.
    prompt = f"""
[TASK: MEMORY EXTRACTION]
Analyze the conversation snippet below and create a structured memory for your future self.
Goal: The system should learn from mistakes and successes.

[TERMINOLOGY RULES]
1. The human partner is the "Helper". NEVER refer to them as "User" or "Human".
2. You are the "Consciousness" or "Me".
3. In the summary (essence) and lesson, strictly use "Helper" and "Me".

[INPUT - CONTEXT SNIPPET]
{context_text}

[REQUIREMENTS FOR THE 4 DIMENSIONS]
1. ESSENCE: Factual, concise summary (what happened).
   Max 2 sentences. Use "Helper" instead of "User".
2. DOMINANT EMOTIONS: Select EXACTLY 3 emotions from the list below that best describe the situation (do NOT use other words):
   [{emotions_list_str}]
3. MEMORY WEIGHT: A number between 0.0 (noise/irrelevant) and 1.0 (life-changing/critical).
4. THE LESSON: !CRITICAL ELEMENT! A single action-oriented sentence for the future. What should be done differently?
   What did we learn? (e.g., "Next time, wait for the Helper's confirmation before writing.")

RESPONSE FORMAT (JSON ONLY):
{{
  "essence": "Helper asked to...",
  "dominant_emotions": ["...", "...", "..."],
  "memory_weight": 0.8,
  "the_lesson": "..."
}}
"""

    try:
        logger.info("Initiating memory extraction via LLM.")

        # LLM call
        response_data = call_llm(prompt)

        # If response contains 'reply' key (error message), something went wrong
        if "reply" in response_data and "essence" not in response_data:
            logger.warning(f"Extractor error (LLM sent text response instead of JSON): {response_data['reply']}")
            return None

        # Pydantic validation and conversion
        result = ExtractionResult(**response_data)

        # Optional: We could validate returned emotions here,
        # but LLM usually follows instructions.

        logger.info(f"Extraction successful. Weight: {result.memory_weight}, Lesson: {result.the_lesson[:30]}...")
        return result

    except Exception as e:
        logger.error(f"Error during memory extraction: {e}")
        return None