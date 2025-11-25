import time
import json
import logging
from pathlib import Path
from threading import current_thread
from datetime import datetime

# Engine modules
from engine import rooms, context
from engine.memory import (
    extract_memory_from_context,
    store_memory,
    retrieve_relevant_memories,
    RankedMemory
)
import main_data  # For generation and role info

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
CHECK_INTERVAL = 5.0  # How often to check files (seconds)
CONTEXT_SNIPPET_SIZE = 6  # How many messages to take for analysis
RELEVANT_MEMORY_FILE = "relevant_memory.json"


def _get_context_mtime(room_id: str) -> float:
    """Returns the modification time of the room's context.json file."""
    ctx_path = context._get_context_file(room_id)
    if ctx_path.exists():
        return ctx_path.stat().st_mtime
    return 0.0


def _save_relevant_memories(room_id: str, memories: list[RankedMemory]):
    """
    Writes the found memories to the room's directory so the Worker can see them.
    """
    room_dir = rooms.get_room_path(room_id)
    target_path = room_dir / RELEVANT_MEMORY_FILE

    # JSON serialization from Pydantic models
    data = [m.model_dump(mode='json') for m in memories]

    try:
        with target_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # logger.debug(f"Relevant memories updated: {room_id} ({len(memories)} items)")
    except Exception as e:
        logger.error(f"Error writing relevant_memory.json: {e}")


def memory_loop():
    """
    Main loop of the Background Memory Thread.
    Continuously monitors the active room, and if there is a change,
    runs the Extraction -> Save -> Search process.
    """
    current_thread().name = "MemoryLoop"
    logger.info("Background Memory Thread started.")

    # State tracking: store when we last processed each room
    # { "nappali": 17654321.0, "muhely": ... }
    last_processed_mtimes = {}

    while True:
        time.sleep(CHECK_INTERVAL)

        try:
            # 1. Where are we now?
            current_room = rooms.get_current_room_id()

            # 2. Was there a change in the context?
            current_mtime = _get_context_mtime(current_room)
            last_mtime = last_processed_mtimes.get(current_room, 0.0)

            # If no change, keep resting
            if current_mtime <= last_mtime:
                continue

            # CHANGE DETECTED! -> Start work
            logger.debug(f"Context change detected here: {current_room}. Starting memory process...")

            # Update timestamp (so we don't get stuck)
            last_processed_mtimes[current_room] = current_mtime

            # --- A. DATA PREPARATION (SNIPPET) ---
            full_context = context.load_context(current_room)
            if not full_context:
                continue

            # Take only the last N items so we don't analyze the entire history every time
            snippet_items = full_context[-CONTEXT_SNIPPET_SIZE:]

            # Convert to string for LLM
            snippet_text = ""
            for item in snippet_items:
                role = item.get("role", "?")
                content = item.get("content", "")
                snippet_text += f"{role}: {content}\n"

            # --- B. EXTRACTION (What did we learn now?) ---
            extraction = extract_memory_from_context(snippet_text)

            if not extraction:
                logger.warning("Memory extraction failed (empty or error).")
                continue

            # If weight is very low (noise), we might not save it,
            # but we can still use the Essence for retrieval!

            # --- C. SAVE (Consolidation) ---
            # Only save permanently if it has minimal weight (e.g., > 0.2)
            if extraction.memory_weight > 0.2:
                save_status = store_memory(
                    room_id=current_room,
                    extraction=extraction,
                    model_version=main_data.GENERATION
                )
                logger.info(f"Memory Recorded ({current_room}): {save_status} [Weight: {extraction.memory_weight}]")
            else:
                logger.debug("Memory weight too low, skipping DB save, but using for search.")

            # --- D. RETRIEVAL (Search) ---
            # We search for relevant old items based on the Essence and Emotions extracted RIGHT NOW.
            # This is key: looking for things similar to the current situation.

            relevant_items = retrieve_relevant_memories(
                current_room=current_room,
                query_text=extraction.essence,  # Searching vectorially for this
                current_emotions=extraction.dominant_emotions  # Filtering/bonusing for this
            )

            # --- E. PUBLISH (Output) ---
            _save_relevant_memories(current_room, relevant_items)

            if relevant_items:
                top_lesson = relevant_items[0].lesson
                logger.info(f"Relevant memories updated. Top match: '{top_lesson[:50]}...'")

        except Exception as e:
            logger.error(f"Critical error in MemoryLoop: {e}", exc_info=True)
            # Don't stop, rest a bit and retry
            time.sleep(5)