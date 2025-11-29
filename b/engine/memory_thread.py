import time
import json
import logging
from threading import current_thread
from datetime import datetime

# Engine modules
# UPDATED: rooms -> modes
from engine import modes, context
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


def _get_context_mtime(mode_id: str) -> float:
    """Returns the modification time of the mode's context.json file."""
    ctx_path = context._get_context_file(mode_id)
    if ctx_path.exists():
        return ctx_path.stat().st_mtime
    return 0.0


def _save_relevant_memories(mode_id: str, memories: list[RankedMemory]):
    """
    Writes the found memories to the mode's directory so the Worker can see them.
    """
    mode_dir = modes.get_mode_path(mode_id)
    target_path = mode_dir / RELEVANT_MEMORY_FILE

    # JSON serialization from Pydantic models
    data = [m.model_dump(mode='json') for m in memories]

    try:
        with target_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error writing relevant_memory.json: {e}")


def memory_loop():
    """
    Main loop of the Background Memory Thread.
    Continuously monitors the active mode, and if there is a change,
    runs the Extraction -> Save -> Search process.
    """
    current_thread().name = "MemoryLoop"
    logger.info("Background Memory Thread started.")

    # State tracking: store when we last processed each mode
    # { "general": 17654321.0, "developer": ... }
    last_processed_mtimes = {}

    while True:
        time.sleep(CHECK_INTERVAL)

        try:
            # 1. Where are we now?
            # UPDATED: room -> mode
            current_mode = modes.get_current_mode_id()

            # 2. Was there a change in the context?
            current_mtime = _get_context_mtime(current_mode)
            last_mtime = last_processed_mtimes.get(current_mode, 0.0)

            # If no change, keep resting
            if current_mtime <= last_mtime:
                continue

            # CHANGE DETECTED! -> Start work
            logger.debug(f"Context change detected here: {current_mode}. Starting memory process...")

            # Update timestamp
            last_processed_mtimes[current_mode] = current_mtime

            # --- A. DATA PREPARATION (SNIPPET) ---
            full_context = context.load_context(current_mode)
            if not full_context:
                continue

            # Take only the last N items
            snippet_items = full_context[-CONTEXT_SNIPPET_SIZE:]

            # Convert to string for LLM (Narrative Format)
            snippet_text = ""
            for item in snippet_items:
                role = item.get("role", "?")
                content = item.get("content", "")

                if role == "user":
                    snippet_text += f"Helper: {content}\n"

                elif role == "assistant":
                    snippet_text += f"Me: {content}\n"

                elif role == "tool" or item.get("type") == "tool_result":
                    try:
                        tool_data = json.loads(content)
                        if isinstance(tool_data, list):
                            for t in tool_data:
                                name = t.get("name", "unknown")
                                args = t.get("args", "{}")
                                output = t.get("output", "")

                                snippet_text += f"I used a tool. Tool: {name}, Args: {args}\n"
                                if output:
                                    snippet_text += f"Result: {output}\n"
                        else:
                            snippet_text += f"Tool usage (raw): {content}\n"

                    except json.JSONDecodeError:
                        snippet_text += f"Tool usage (error parsing): {content}\n"

                elif role == "system":
                    snippet_text += f"[System Event]: {content}\n"

                else:
                    snippet_text += f"[{role}]: {content}\n"

            # --- B. EXTRACTION (What did we learn now?) ---
            extraction = extract_memory_from_context(snippet_text)

            if not extraction:
                logger.warning("Memory extraction failed (empty or error).")
                continue

            # --- C. SAVE (Consolidation) ---
            if extraction.memory_weight > 0.2:
                # UPDATED: room_id -> mode_id
                save_status = store_memory(
                    mode_id=current_mode,
                    extraction=extraction,
                    model_version=main_data.GENERATION
                )
                logger.info(f"Memory Recorded ({current_mode}): {save_status} [Weight: {extraction.memory_weight}]")
            else:
                logger.debug("Memory weight too low, skipping DB save, but using for search.")

            # --- D. RETRIEVAL (Search) ---
            # Search for relevant old items based on the Essence and Emotions extracted RIGHT NOW.
            # UPDATED: current_room -> current_mode
            relevant_items = retrieve_relevant_memories(
                current_mode=current_mode,
                query_text=extraction.essence,
                current_emotions=extraction.dominant_emotions
            )

            # --- E. PUBLISH (Output) ---
            _save_relevant_memories(current_mode, relevant_items)

            if relevant_items:
                top_lesson = relevant_items[0].lesson
                logger.info(f"Relevant memories updated. Top match: '{top_lesson[:50]}...'")

        except Exception as e:
            logger.error(f"Critical error in MemoryLoop: {e}", exc_info=True)
            time.sleep(5)