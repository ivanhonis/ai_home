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
        room_id: str,
        extraction: ExtractionResult,
        model_version: str = "Unknown"
) -> str:
    """
    Saves the extracted memory into the database.
    Automatically generates embedding and handles deduplication.
    """
    logger.info(f"Attempting to store memory for Room: {room_id}")

    # 1. Generate Embedding (Google text-embedding-005)
    # This is a network call, so we do it explicitly first
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
            # Check if a very similar memory already exists IN THE SAME ROOM.
            # (The <=> operator returns distance. Similarity = 1 - Distance)

            dist_limit = 1.0 - MemoryConfig.DEDUPLICATION_THRESHOLD

            cur.execute("""
                SELECT id, (embedding <=> %s::vector) as distance
                FROM memories
                WHERE room_id = %s
                ORDER BY distance ASC
                LIMIT 1;
            """, (embedding_vector, room_id))

            row = cur.fetchone()

            if row:
                existing_id, existing_dist = row
                if existing_dist < dist_limit:
                    # Too similar -> Do not save as new, but reinforce the old one
                    logger.info(f"Duplication avoided (Dist: {existing_dist:.4f}). Reinforcing existing memory.")

                    # Increment counter and update last access time
                    cur.execute("""
                        UPDATE memories 
                        SET access_count = access_count + 1, last_accessed = NOW()
                        WHERE id = %s
                    """, (existing_id,))

                    return "DUPLICATION: Similar memory already exists. Reinforced."

            # 3. Save (INSERT)
            # psycopg2 automatically converts dominant_emotions list to Postgres ARRAY
            cur.execute("""
                INSERT INTO memories 
                (room_id, model_version, essence, dominant_emotions, memory_weight, the_lesson, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                room_id,
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
        current_room: str,
        query_text: str,
        current_emotions: List[str] = None
) -> List[RankedMemory]:
    """
    Hybrid Retrieval:
    1. Vector filtering in the database (Room ID logic).
    2. Detailed scoring and ranking on Python side.
    3. Reinforcement of selected memories (Update).
    """
    if not query_text:
        return []

    logger.info(f"Retrieving memories for Room: {current_room}, Query: '{query_text[:20]}...'")

    # 1. Embedding for the search term (usually the current Essence)
    try:
        query_vector = get_embedding(query_text)
    except Exception as e:
        logger.error(f"Embedding failed during retrieval: {e}")
        return []

    if not query_vector:
        return []

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            # 2. SQL QUERY (Selecting Candidates)
            # Implementing Visibility Matrix here.

            room_filter = ""
            params: List[object] = [query_vector]

            if current_room == "nappali":  # 'nappali' is kept as specific room ID
                # LIVING ROOM (Global): Sees everything (No room filter)
                room_filter = "1=1"
            else:
                # LOCAL ROOM: Sees its own + the Living Room
                room_filter = "(room_id = %s OR room_id = 'nappali')"
                params.append(current_room)

            # Retrieve TOP N candidates based on vector similarity
            sql = f"""
                SELECT 
                    id, essence, the_lesson, dominant_emotions, memory_weight, 
                    created_at, access_count, room_id,
                    1 - (embedding <=> %s::vector) as similarity
                FROM memories
                WHERE {room_filter}
                ORDER BY similarity DESC
                LIMIT {MemoryConfig.RETRIEVAL_CANDIDATE_LIMIT};
            """

            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

            # 3. PYTHON RANKING (Scoring)
            ranked_candidates = []

            for row in rows:
                mid, essence, lesson, emotions, weight, created_at, access_count, rid, sim = row

                # Null check
                if emotions is None: emotions = []
                if weight is None: weight = 0.5

                # Calculate sub-scores
                recency = calculate_recency_score(created_at)
                freq = calculate_frequency_score(access_count)

                # Check for emotional overlap
                has_emotional_overlap = False
                if current_emotions and emotions:
                    # Lowercase set operation
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
                    id=str(mid),
                    essence=essence,
                    lesson=lesson,
                    emotions=emotions,
                    score=final_score,
                    room_id=rid,
                    created_at=created_at,
                    usage_count=access_count
                ))

            # 4. SELECTION (Top N)
            ranked_candidates.sort(key=lambda x: x.score, reverse=True)
            final_selection = ranked_candidates[:MemoryConfig.FINAL_RESULT_LIMIT]

            # 5. REINFORCEMENT
            # The selected memories were important, increase their weight for the future
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