import json
import logging
from typing import Any, Dict, List
from queue import Queue

# --------------------------------------------------------------------
# IMPORT MODULES
# --------------------------------------------------------------------
from engine.llm import call_llm
from engine.tools import dispatch_tools
from engine import mind as mind_lib

# Importing from prompts package
from prompts import build_reactive_prompt, build_proactive_prompt

# Global data and helpers from the new module
import main_data

# Global constants from main_data
ROLE_ID = main_data.ROLE_ID
GENERATION = main_data.GENERATION
ROLE_NAME = main_data.ROLE_NAME_MAP.get(ROLE_ID, "UNKNOWN")

logger = logging.getLogger(__name__)


def worker_loop(task_queue: Queue, result_queue: Queue):
    """
    The 'Brain' running in the background.
    Responsible for processing incoming tasks (LLM calls, tool execution).
    """
    logger.info("Worker thread started.")

    while True:
        task = task_queue.get()
        if task is None:
            break  # Shutdown

        try:
            # Check where we are before every task
            current_room = main_data.rooms.get_current_room_id()
            current_intent = main_data.rooms.get_current_intent()

            # Load data (Now without legacy memory)
            data = main_data.load_all_context_data(current_room)

            # --- PROCESS SUBCONSCIOUS MESSAGES LIST ---
            mono_raw = data.get("monologue_data", [])
            if isinstance(mono_raw, dict):
                mono_raw = [mono_raw]

            messages_list = []
            for item in mono_raw:
                raw_ts = item.get("timestamp", "")
                ts = raw_ts[11:16] if len(raw_ts) >= 16 else ""
                msg = item.get("message", "")
                if msg:
                    messages_list.append(f"[{ts}] {msg}")

            monologue_message = "\n".join(messages_list) if messages_list else ""

            prompt = ""
            task_type = task.get("type")

            # --- A: USER MESSAGE OR CONTINUATION AFTER TOOL (REACTIVE) ---
            if task_type in ["user_message", "llm_call_after_tool"]:
                logger.debug(f"Worker: Reactive thinking ({current_room})")

                user_msg = task.get("content", None)

                # 1. INTERNAL THINKING AND PLANNING (MIND.PY CALL)
                # Passing relevant memories to MIND instead of the old list
                thought = mind_lib.internal_thought(
                    identity=data["identity"],
                    memory=data["relevant_memories"],
                    context=data["local_context"],
                    user_input=user_msg if user_msg else "Reflection after tool execution."
                )

                internal_plan = thought.get("plan", "")
                internal_essence = thought.get("essence", "")

                # 2. EXTERNAL RESPONSE GENERATION
                prompt = build_reactive_prompt(
                    room_id=current_room,
                    generation=GENERATION,
                    role_name=ROLE_NAME,
                    intent=current_intent,
                    identity=data["identity"],
                    relevant_memories=data["relevant_memories"],
                    use_data=data["use_data"],
                    global_context_tail=data["global_context_tail"],
                    local_context=data["local_context"],
                    user_message=user_msg,
                    internal_plan=internal_plan,
                    internal_essence=internal_essence,
                    monologue_message=monologue_message
                )

                llm_response = call_llm(prompt)
                result_queue.put({"type": "llm_result", "data": llm_response, "room_id": current_room})

            # --- B: TOOL CALL EXECUTION ---
            elif task_type == "tool_call":
                logger.debug(f"Worker: Tool execution ({current_room})")
                tools_to_run = task.get("tools", [])

                tool_results = dispatch_tools(
                    tools_to_run,
                    generation=GENERATION,
                    role=ROLE_ID,
                    slot=main_data.BASE_DIR.name,
                    current_room=current_room
                )

                result_queue.put({"type": "tool_result", "data": tool_results, "room_id": current_room})

            # --- C: PROACTIVE THINKING ---
            elif task_type == "proactive_thought":
                logger.debug(f"Worker: Proactive thinking ({current_room})")

                thought_input = f"Internal reflection needed. My current intent: {current_intent}. Evaluate the situation and create a plan."

                thought = mind_lib.internal_thought(
                    identity=data["identity"],
                    memory=data["relevant_memories"],
                    context=data["local_context"],
                    user_input=thought_input
                )

                internal_plan = thought.get("plan", "")
                internal_essence = thought.get("essence", "")

                prompt = build_proactive_prompt(
                    room_id=current_room,
                    generation=GENERATION,
                    role_name=ROLE_NAME,
                    intent=current_intent,
                    identity=data["identity"],
                    relevant_memories=data["relevant_memories"],
                    use_data=data["use_data"],
                    global_context_tail=data["global_context_tail"],
                    local_context=data["local_context"],
                    internal_plan=internal_plan,
                    internal_essence=internal_essence,
                    monologue_message=monologue_message
                )

                llm_response = call_llm(prompt)
                result_queue.put({"type": "llm_result", "data": llm_response, "room_id": current_room})

        except Exception as e:
            logger.error(f"Error in Worker: {e}", exc_info=True)
            result_queue.put({"type": "error", "message": str(e)})

        finally:
            task_queue.task_done()

    logger.info("Worker thread stopped.")