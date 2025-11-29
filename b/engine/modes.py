import json
from pathlib import Path
from typing import Dict, Any, List
from .files import save_json, load_json

# ====================================================================
# OPERATING MODES CONFIGURATION (MODE_CONFIG)
# ====================================================================

MODE_CONFIG = {
    "general": {
        "name": "General Mode",
        "description": "Primary operating mode. Global decisions, conversation, and coordination.",
        "type": "global",
        "path": "modes/general",
        "allowed_tools": [
            "flow.*",
            "knowledge.*",
            "game.*",
            "info.*",
            "system.log_event"
        ]
    },
    "developer": {
        "name": "Developer Mode",
        "description": "Engineering context. Code modification, file system access, and technical implementation.",
        "type": "local",
        "path": "modes/developer",
        "allowed_tools": [
            "flow.*",
            "knowledge.*",
            "game.*",
            "info.*",
            "system.*"  # Full system access (files, dumps, etc.)
        ]
    },
    "analyst": {
        "name": "Analyst Mode",
        "description": "Deep thinking context. Analysis, planning, and strategy without modification risks.",
        "type": "local",
        "path": "modes/analyst",
        "allowed_tools": [
            "flow.*",
            "knowledge.*",
            "game.*",
            "info.*"
            # No system write access here
        ]
    },
    "game": {
        "name": "Game Mode",
        "description": "A playground for the mind. Dedicated to relaxation, roleplay, and testing personas. Disconnected from work responsibilities.",
        "type": "local",
        "path": "modes/game",
        "allowed_tools": [
            "flow.*",
            "game.*",
            "knowledge.recall_emotion",
            "info.*"
        ]
    }
}

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "state.json"


# ====================================================================
# STATE MANAGEMENT (STATE)
# ====================================================================

def init_state() -> Dict[str, Any]:
    """
    Loads or creates state.json.
    Defaults to 'general' mode.
    """
    default_state = {
        "current_mode": "general",
        "current_intent": "System Startup: Waiting for user input.",
        "incoming_summary": "",
        "last_active": ""
    }
    return load_json("state.json", default_state)


def save_state(state: Dict[str, Any]):
    save_json("state.json", state)


def get_current_mode_id() -> str:
    state = init_state()
    # Fallback: if 'current_mode' is missing, default to 'general'
    mid = state.get("current_mode", "general")

    if mid not in MODE_CONFIG:
        return "general"
    return mid


def get_current_intent() -> str:
    state = init_state()
    return state.get("current_intent", "")


def get_incoming_summary() -> str:
    state = init_state()
    return state.get("incoming_summary", "")


def update_state(mode_id: str, intent: str, summary: str = ""):
    """
    Updates the active mode, intent, and optionally the summary.
    Also cleans up legacy 'current_room' key if present.
    """
    state = init_state()
    state["current_mode"] = mode_id
    state["current_intent"] = intent

    if summary:
        state["incoming_summary"] = summary

    # Cleanup legacy key
    if "current_room" in state:
        del state["current_room"]

    save_state(state)


def clear_incoming_summary():
    state = init_state()
    state["incoming_summary"] = ""
    save_state(state)


# ====================================================================
# HELPER FUNCTIONS
# ====================================================================

def get_mode_config(mode_id: str) -> Dict[str, Any]:
    return MODE_CONFIG.get(mode_id, MODE_CONFIG["general"])


def get_allowed_tools(mode_id: str) -> List[str]:
    """Returns the names of allowed tools in the given mode."""
    cfg = get_mode_config(mode_id)
    return cfg.get("allowed_tools", [])


def get_mode_path(mode_id: str) -> Path:
    """
    Returns the Path object for the mode's physical directory.
    Creates the folder if it does not exist.
    """
    cfg = get_mode_config(mode_id)
    rel_path = cfg.get("path", "modes/general")
    full_path = BASE_DIR / rel_path
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path


def validate_target_mode(mode_id: str) -> bool:
    return mode_id in MODE_CONFIG