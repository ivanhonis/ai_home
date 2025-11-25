from typing import Dict, Any
from engine.rooms import ROOM_CONFIG, get_current_room_id, update_state


def switch_room(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context Switching (Room Change).
    If the target room is the same as current, returns in silent mode.
    """
    target_room = args.get("target_room")
    intent = args.get("intent", "No intent specified.")
    summary = args.get("summary", "")

    if not target_room:
        return {"content": "ERROR: 'target_room' is mandatory.", "silent": False}

    if target_room not in ROOM_CONFIG:
        return {
            "content": f"ERROR: Invalid target room: '{target_room}'. Available: {list(ROOM_CONFIG.keys())}",
            "silent": False
        }

    current_actual_room = get_current_room_id()

    # Filter redundant switching
    if target_room == current_actual_room:
        return {
            "content": f"INFO: Switch not necessary, you are already in room '{target_room}'.",
            "silent": True
        }

    # Real switch: Update state
    update_state(target_room, intent, summary)

    return {
        "content": f"Switch initiated successfully. Target: {target_room}. Intent: {intent}.",
        "silent": False
    }


def continue_process(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforcing Dynamic Silence Protocol:
    Instructs the system to immediately recall the LLM for the next step.
    """
    next_step = args.get("next_step_description", "Continuing the logical chain.")

    # silent=False guarantees LLM recall in the Worker
    return {
        "content": f"Continuation enforced. Intent for next cycle: {next_step}",
        "silent": False
    }