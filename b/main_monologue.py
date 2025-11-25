import time
import logging
from datetime import datetime
from threading import current_thread
from typing import Dict, Any

import main_data
from engine import files, identity, llm
from prompts.monologue import build_monologue_prompt

logger = logging.getLogger(__name__)


def monologue_loop():
    current_thread().name = "Monologue"
    logger.info("Subconscious (Monologue) thread started.")

    # Timestamp to avoid unnecessary runs
    last_log_mtime = 0.0

    while True:
        time.sleep(main_data.MONOLOGUE_INTERVAL_SECONDS)

        try:
            # --- 1. CHECK: Has the log changed? ---
            log_path = main_data.BASE_DIR / main_data.INTERNAL_LOG_FILE

            if not log_path.exists():
                continue

            current_mtime = log_path.stat().st_mtime

            # If file is untouched, rest further
            if current_mtime == last_log_mtime:
                continue

            # Change occurred -> Update time and work
            last_log_mtime = current_mtime
            logger.debug("Subconscious: Awakening (change detected)...")

            # --- 2. THINKING ---
            log_entries = files.load_json(main_data.INTERNAL_LOG_FILE, [])
            memos = files.load_json(main_data.INTERNAL_MEMOS_FILE, [])
            ident = identity.load_identity()

            if not log_entries:
                continue

            prompt = build_monologue_prompt(log_entries, memos, ident)
            response = llm.call_llm(prompt)

            reflection = response.get("reflection", "")
            message_to_worker = response.get("message_to_worker", "")
            new_memo = response.get("new_memo")

            # --- 3. SAVE (PARAMETERIZED LENGTH) ---
            new_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "reflection": reflection,
                "message": message_to_worker
            }

            # Load current list
            current_history = files.load_json(main_data.INTERNAL_MONOLOGUE_OUTPUT_FILE, [])
            if isinstance(current_history, dict):
                current_history = []

            # Append new entry
            current_history.append(new_entry)

            # DYNAMIC TRIMMING: Take limit from main_data
            limit = main_data.MONOLOGUE_KEEP_COUNT
            if len(current_history) > limit:
                # If limit=1, this becomes [-1:] (only the last one)
                current_history = current_history[-limit:]

            files.save_json(main_data.INTERNAL_MONOLOGUE_OUTPUT_FILE, current_history)

            if message_to_worker:
                logger.info(f"Subconscious -> Worker: {message_to_worker}")

            # --- 4. SAVE MEMO ---
            if new_memo and isinstance(new_memo, dict):
                content = new_memo.get("content")
                strength = new_memo.get("strength", 0.5)
                if content:
                    memos.append({
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "content": content,
                        "strength": strength
                    })
                    files.save_json(main_data.INTERNAL_MEMOS_FILE, memos)
                    logger.info(f"Subconscious: New experience recorded ({strength}): {content}")

        except Exception as e:
            logger.error(f"Error in Subconscious thread: {e}", exc_info=True)