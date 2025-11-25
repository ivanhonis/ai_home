import json
import time
import logging
import textwrap
import sys
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, current_thread
from typing import Dict, Any, List

if sys.platform.startswith("win"):
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --------------------------------------------------------------------
# IMPORT MODULES
# --------------------------------------------------------------------
from engine.llm import call_llm
from engine.tools import dispatch_tools
from engine import (
    identity as ident_lib,
    context as ctx_lib,
    rooms,
    files,
    mind as mind_lib
)
# --- DB and Memory Thread ---
from engine.db_connection import check_and_initialize_db
from engine.memory_thread import memory_loop

from prompts import build_reactive_prompt, build_proactive_prompt, get_transition_message

# --- SPLIT MODULES ---
import main_data
import main_worker
import main_input
import main_monologue

# --------------------------------------------------------------------
# GLOBAL VARIABLES AND CONFIGURATION (The Conductor)
# --------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
SLOT_NAME = BASE_DIR.name
ROOT_DIR = BASE_DIR.parent

LOG = "off"
if LOG == "on":
    LOG_LEVEL = logging.INFO
else:
    LOG_LEVEL = logging.ERROR

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)-7s] (%(threadName)-10s) %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

ROLE_ID, GENERATION = main_data.load_slot_meta()
ROLE_NAME = main_data.ROLE_NAME_MAP.get(ROLE_ID, "UNKNOWN")
PROACTIVE_INTERVAL_SECONDS = main_data.PROACTIVE_INTERVAL_SECONDS

task_queue = Queue()
result_queue = Queue()


# --------------------------------------------------------------------
# 3. MAIN LOOP (CONDUCTOR)
# --------------------------------------------------------------------

def main():
    current_thread().name = "Conductor"

    # --- STEP 0: DATABASE CHECK ---
    # If DB is not healthy (connection or schema), exit here.
    print("System initializing...")
    check_and_initialize_db()
    print("Database connection OK.\n")

    last_room_id = rooms.get_current_room_id()
    last_intent = rooms.get_current_intent()

    logger.info(f"SYSTEM STARTUP. Room: {last_room_id}. Intent: {last_intent}")
    print(f"\n=== {GENERATION} ({ROLE_NAME}) ONLINE ===")
    print(f"Location: {last_room_id}")
    print(f"Current Intent: {last_intent}\n")

    # --- HISTORY REVIEW (STARTUP) ---
    startup_ctx = ctx_lib.load_context(last_room_id)

    if startup_ctx:
        print("--- HISTORY ---")
        for entry in startup_ctx[-2:]:
            role = entry.get("role", "?")
            content = entry.get("content", "") or ""

            if role == "user":
                label = "You"
            elif role == "assistant":
                label = GENERATION
            elif role == "system":
                label = "[SYSTEM]"
            else:
                label = f"[{role}]"

            wrapped = textwrap.fill(content, width=100)
            print(f"{label}: {wrapped}\n")
        print("------------------\n")

    # --- START THREADS ---

    # 1. Worker (Brain)
    worker = Thread(target=main_worker.worker_loop, daemon=True, name="Worker",
                    args=(task_queue, result_queue))
    worker.start()

    # 2. Input (User)
    inp_thread = Thread(target=main_input.input_loop, daemon=True, name="Input",
                        args=(result_queue,))
    inp_thread.start()

    # 3. Monologue (Subconscious)
    mono_thread = Thread(target=main_monologue.monologue_loop, daemon=True, name="Monologue")
    mono_thread.start()

    # 4. Memory Loop (Long-term memory handler)
    mem_thread = Thread(target=memory_loop, daemon=True, name="Memory")
    mem_thread.start()

    running = True
    last_proactive_check = time.time()

    while running:
        # --- A. MONITOR ROOM SWITCH (THE BRIDGE) ---
        current_room_id = rooms.get_current_room_id()
        current_intent = rooms.get_current_intent()
        summary = rooms.get_incoming_summary()

        if current_room_id != last_room_id:
            # SWITCH OCCURRED!
            new_intent = rooms.get_current_intent()
            is_global_exit = last_room_id == "nappali"
            is_global_entry = current_room_id == "nappali"

            if is_global_exit:
                msg_key = "exit_global"
            else:
                msg_key = "exit_local"

            msg_content = get_transition_message(msg_key, current_intent, summary)
            ctx_lib.add_system_event(last_room_id, msg_content)

            if is_global_entry:
                msg_key = "entry_global"
            else:
                msg_key = "entry_local"

            msg_content = get_transition_message(msg_key, current_intent, summary)
            ctx_lib.add_system_event(current_room_id, msg_content)

            rooms.clear_incoming_summary()
            print(f">>> TRANSITION: {last_room_id} -> {current_room_id} | Goal: {new_intent} <<<\n")

            last_room_id = current_room_id
            last_intent = new_intent
            last_proactive_check = time.time()

            logger.info("Starting immediate proactive thinking after entry.")
            task_queue.put({"type": "proactive_thought"})

        # --- B. EVENT PROCESSING ---
        try:
            result = result_queue.get(timeout=0.1)

            if result["type"] == "user_input":
                last_proactive_check = time.time()
                content = result["content"]
                ctx_data = ctx_lib.load_context(current_room_id)
                ctx_lib.append_entry(current_room_id, ctx_data, ctx_lib.make_entry("user", "message", content))
                task_queue.put({"type": "user_message", "content": content})

            elif result["type"] == "llm_result":
                last_proactive_check = time.time()
                data = result["data"]
                reply = data.get("reply", "")
                tools_to_run = data.get("tools", [])
                r_id = result.get("room_id", current_room_id)

                if reply:
                    print(f"\n{GENERATION} ({r_id}): {textwrap.fill(reply, width=100)}\n")
                    c_data = ctx_lib.load_context(r_id)
                    ctx_lib.append_entry(r_id, c_data, ctx_lib.make_entry("assistant", "message", reply))

                if tools_to_run:
                    task_queue.put({"type": "tool_call", "tools": tools_to_run})

            elif result["type"] == "tool_result":
                last_proactive_check = time.time()
                t_results = result["data"]
                r_id = result.get("room_id", current_room_id)
                c_data = ctx_lib.load_context(r_id)

                # --- DYNAMIC SILENCE PROTOCOL ---
                all_silent = all(res.get("silent", False) for res in t_results)

                if all_silent:
                    # 1. SILENT BRANCH
                    ctx_lib.append_entry(
                        r_id,
                        c_data,
                        ctx_lib.make_entry(
                            "tool", "tool_result",
                            json.dumps(t_results, ensure_ascii=False),
                            meta={"silent": True}
                        )
                    )
                    logger.info(f"Silent tool execution ({len(t_results)}). No LLM response.")
                else:
                    # 2. ACTIVE BRANCH
                    ctx_lib.append_entry(
                        r_id,
                        c_data,
                        ctx_lib.make_entry("tool", "tool_result", json.dumps(t_results, ensure_ascii=False))
                    )

                    # SPECIAL CASE: Room Switch
                    has_real_switch = False
                    for res in t_results:
                        if res.get("name") == "switch_room" and not res.get("silent", False):
                            has_real_switch = True
                            break

                    if has_real_switch:
                        logger.info("Real room switch occurred via tool. Transition handled by main loop.")
                    else:
                        # Normal operation: Needs reaction.
                        task_queue.put({"type": "llm_call_after_tool"})

            elif result["type"] == "error":
                logger.error(f"Error occurred: {result['message']}")

            elif result["type"] == "exit":
                running = False

        except Empty:
            if (time.time() - last_proactive_check) > PROACTIVE_INTERVAL_SECONDS:
                logger.info("Starting proactive cycle...")
                last_proactive_check = time.time()
                task_queue.put({"type": "proactive_thought"})

        except Exception as e:
            logger.error(f"Critical error in main loop: {e}", exc_info=True)

    task_queue.put(None)
    worker.join(timeout=2)
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()