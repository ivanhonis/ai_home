from typing import Dict, Any
# UPDATED: rooms -> modes
from engine.modes import MODE_CONFIG, get_current_mode_id, update_state

def switch_mode(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Switches the operating mode of the agent.
    Renamed from switch_room.
    """
    target_mode = args.get("target_mode")
    intent = args.get("intent", "No intent")
    summary = args.get("summary", "")

    if not target_mode or target_mode not in MODE_CONFIG:
        return {"content": f"Error: Invalid mode '{target_mode}'", "silent": False}

    current = get_current_mode_id()
    if target_mode == current:
         return {"content": "Already in this mode.", "silent": True}

    update_state(target_mode, intent, summary)
    return {"content": f"Switched to {target_mode}. Intent: {intent}", "silent": False}


def continue_process(args: Dict[str, Any]) -> Dict[str, Any]:
    next_step = args.get("next_step", "Continuing...")
    return {"content": f"Continuing: {next_step}", "silent": False}