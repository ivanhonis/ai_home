# ================================================================================
# FILE: b/engine/memory/manager.py
# ================================================================================

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from engine.db_connection import get_db_connection
from engine.llm import get_embedding

from .config import MemoryConfig
from .models import ExtractionResult, RankedMemory
from .scoring import (
    calculate_recency_score,
    calculate_frequency_score,
    calculate_final_score
)

logger = logging.getLogger(__name__)


def store_memory(
        mode_id: str,
        extraction: ExtractionResult,
        model_version: str = "Unknown"
) -> str:
    """
    Saves the extracted memory into the database.
    Automatically generates embedding and handles deduplication.
    UPDATED: room_id -> mode_id
    """
    logger.info(f"Attempting to store memory for Mode: {mode_id}")

    # 1. Generate Embedding (Google text-embedding-005)
    try:
        embedding_vector = get_embedding(extraction.essence)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return f"ERROR: Embedding generation failed: {e}"

    if not embedding_vector:
        logger.error("Generated embedding is empty.")
        return "ERROR: Embedding is empty."

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 2. Check Deduplication
            # Check if a very similar memory already exists IN THE SAME MODE.
            dist_limit = 1.0 - MemoryConfig.DEDUPLICATION_THRESHOLD

            cur.execute("""
                SELECT id, (embedding <=> %s::vector) as distance
                FROM memories
                WHERE mode_id = %s
                ORDER BY distance ASC
                LIMIT 1;
            """, (embedding_vector, mode_id))

            row = cur.fetchone()

            if row:
                existing_id, existing_dist = row
                if existing_dist < dist_limit:
                    # Too similar -> Do not save as new, but reinforce the old one
                    logger.info(f"Duplication avoided (Dist: {existing_dist:.4f}). Reinforcing existing memory.")

                    cur.execute("""
                        UPDATE memories 
                        SET access_count = access_count + 1, last_accessed = NOW()
                        WHERE id = %s
                    """, (existing_id,))

                    return "DUPLICATION: Similar memory already exists. Reinforced."

            # 3. Save (INSERT)
            cur.execute("""
                INSERT INTO memories 
                (mode_id, model_version, essence, dominant_emotions, memory_weight, the_lesson, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                mode_id,
                model_version,
                extraction.essence,
                extraction.dominant_emotions,
                extraction.memory_weight,
                extraction.the_lesson,
                embedding_vector
            ))

            logger.info("New memory successfully inserted.")

        return "SUCCESS: New memory recorded."

    except Exception as e:
        logger.error(f"DB error during store_memory: {e}")
        return f"DB ERROR: {e}"
    finally:
        conn.close()


def retrieve_relevant_memories(
        current_mode: str,
        query_text: str,
        current_emotions: List[str] = None,
        exact_emotions_only: bool = False
) -> List[RankedMemory]:
    """
    Hybrid Retrieval:
    1. Vector filtering in the database (Mode ID logic).
    2. Detailed scoring and ranking on Python side.

    UPDATED: Supports 'exact_emotions_only' mode which bypasses vector search
    and uses SQL Array Overlap (&&) operator for strict emotion filtering.
    """

    # If no query and no exact emotion filter, nothing to do
    if not query_text and not exact_emotions_only:
        return []

    logger.info(
        f"Retrieving memories. Mode: {current_mode}, ExactEmotion: {exact_emotions_only}, Query: '{query_text[:20]}...'")

    # 1. Embedding Strategy
    query_vector = None

    # Only generate embedding if we are NOT in exact mode, or if we have text we want to use for scoring
    # In exact mode, query_text is usually empty/ignored for vector search, so we skip to save API calls.
    if not exact_emotions_only and query_text:
        try:
            query_vector = get_embedding(query_text)
        except Exception as e:
            logger.error(f"Embedding failed during retrieval: {e}")
            return []

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            # 2. SQL QUERY CONSTRUCTION

            # Base Where Clause (Mode Logic)
            # GENERAL sees everything, LOCAL sees LOCAL + GENERAL
            if current_mode == "general":
                where_sql = "1=1"
                params = []
            else:
                where_sql = "(mode_id = %s OR mode_id = 'general')"
                params = [current_mode]

            # --- BRANCH A: EXACT EMOTION FILTER ---
            if exact_emotions_only:
                if not current_emotions:
                    logger.warning("Exact emotion search requested but list is empty.")
                    return []

                # Append SQL Array Overlap condition
                where_sql += " AND dominant_emotions && %s::text[]"
                params.append(current_emotions)

                # In exact mode, we don't use vector distance.
                # We return 1.0 as similarity (perfect match criteria) so the scorer doesn't penalize it.
                # We order by CREATED_AT DESC (Recency) to get the newest relevant emotions.
                sql = f"""
                    SELECT 
                        id, essence, the_lesson, dominant_emotions, memory_weight, 
                        created_at, access_count, mode_id,
                        1.0 as similarity
                    FROM memories
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT {MemoryConfig.RETRIEVAL_CANDIDATE_LIMIT};
                """

            # --- BRANCH B: VECTOR SEARCH ---
            else:
                if not query_vector:
                    return []

                # Standard Vector Distance (Cosine)
                # Params order: [query_vector, (mode_id...), ...]
                # We need to restructure params because vector comes first for distance calculation logic usually,
                # but let's just use Python list building carefully.

                # Reset params for vector path to be clean
                vec_params = [query_vector]
                if current_mode != "general":
                    vec_params.append(current_mode)

                sql = f"""
                    SELECT 
                        id, essence, the_lesson, dominant_emotions, memory_weight, 
                        created_at, access_count, mode_id,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM memories
                    WHERE {where_sql}
                    ORDER BY similarity DESC
                    LIMIT {MemoryConfig.RETRIEVAL_CANDIDATE_LIMIT};
                """
                params = vec_params

            # Execute
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

            # 3. PYTHON RANKING (Scoring)
            ranked_candidates = []

            for row in rows:
                mid_val, essence, lesson, emotions, weight, created_at, access_count, mode_id_val, sim = row

                # Null check
                if emotions is None: emotions = []
                if weight is None: weight = 0.5

                # Calculate sub-scores
                recency = calculate_recency_score(created_at)
                freq = calculate_frequency_score(access_count)

                # Check for emotional overlap (Bonus)
                # Even in exact mode, we calculate this to give the slight bonus in the final formula
                has_emotional_overlap = False
                if current_emotions and emotions:
                    curr_set = {e.lower() for e in current_emotions}
                    mem_set = {e.lower() for e in emotions}
                    if not curr_set.isdisjoint(mem_set):
                        has_emotional_overlap = True

                # Calculate final score
                final_score = calculate_final_score(
                    sim_score=float(sim),
                    internal_weight=float(weight),
                    recency_score=recency,
                    freq_score=freq,
                    has_emotional_overlap=has_emotional_overlap
                )

                ranked_candidates.append(RankedMemory(
                    id=str(mid_val),
                    essence=essence,
                    lesson=lesson,
                    emotions=emotions,
                    score=final_score,
                    mode_id=mode_id_val,
                    created_at=created_at,
                    usage_count=access_count
                ))

            # 4. SELECTION (Top N)
            ranked_candidates.sort(key=lambda x: x.score, reverse=True)
            final_selection = ranked_candidates[:MemoryConfig.FINAL_RESULT_LIMIT]

            # 5. REINFORCEMENT
            if final_selection:
                ids_to_update = [m.id for m in final_selection]
                cur.execute("""
                    UPDATE memories
                    SET access_count = access_count + 1, last_accessed = NOW()
                    WHERE id = ANY(%s::uuid[])
                """, (ids_to_update,))

            logger.info(f"Retrieved {len(final_selection)} relevant memories.")
            return final_selection

    except Exception as e:
        logger.error(f"Error during retrieve_relevant_memories: {e}")
        return []
    finally:
        conn.close()