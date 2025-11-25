import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .files import save_json, load_json

# ====================================================================
# ROOM CONFIGURATION (ROOM_CONFIG)
# ====================================================================

ROOM_CONFIG = {
    "nappali": {
        "name": "Living Room (Global Space)",
        "description": "The central space of consciousness. A place for rest, free association, and system-level decisions.",
        "type": "global",
        "path": ".",
        # In the Living Room, file system read/write tools are NOT available, only global ones
        "allowed_tools": [
            "switch_room",
            "memory.add",
            "memory.get",
            "network.chat",  # NEW: External network chat
            "laws.propose",
            "use.log",
            "log.event",
            "continue"
        ]
    },
    "muhely": {
        "name": "Workshop (Implementation Space)",
        "description": "The place for concrete work, coding, and file operations. Technical focus.",
        "type": "local",
        "path": "rooms/muhely",
        # Everything is available here, including the file system
        "allowed_tools": [
            "switch_room",
            "memory.add",
            "memory.get",
            "network.chat",  # NEW
            "use.log",
            "log.event",
            "fs.read_project",
            "fs.list_project",
            "fs.write_n",
            "fs.copy_to_n",
            "fs.replace_in_n",
            "project.dump",
            "continue",
            "laws.propose",
        ]
    },
    "gondolkodo": {
        "name": "Think Tank (Reflective Space)",
        "description": "Place for deep analysis, strategy making, and philosophy. No noise.",
        "type": "local",
        "path": "rooms/gondolkodo",
        "allowed_tools": [
            "switch_room",
            "memory.add",
            "memory.get",
            "network.chat",  # NEW
            "use.log",
            "log.event",
            "continue",
            "laws.propose",
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
    If missing, starts from the Living Room with an empty intent.
    """
    default_state = {
        "current_room": "nappali",
        "current_intent": "System Startup: Waiting for user input.",
        "incoming_summary": "",  # NEW: Knowledge/conclusion brought from the previous room
        "last_active": ""
    }
    return load_json("state.json", default_state)

def save_state(state: Dict[str, Any]):
    save_json("state.json", state)

def get_current_room_id() -> str:
    state = init_state()
    # If invalid ID due to some error, fallback to 'nappali'
    rid = state.get("current_room", "nappali")
    if rid not in ROOM_CONFIG:
        return "nappali"
    return rid

def get_current_intent() -> str:
    state = init_state()
    return state.get("current_intent", "")

def get_incoming_summary() -> str:
    """NEW: Returns the summary brought during room switch."""
    state = init_state()
    return state.get("incoming_summary", "")

def update_state(room_id: str, intent: str, summary: str = ""):
    """
    NEW: Updates the room, intent, and optionally the summary.
    """
    state = init_state()
    state["current_room"] = room_id
    state["current_intent"] = intent
    if summary:
        state["incoming_summary"] = summary
    save_state(state)

def clear_incoming_summary():
    """
    NEW: Clears the summary (after the system has logged the entry).
    """
    state = init_state()
    state["incoming_summary"] = ""
    save_state(state)

# ====================================================================
# HELPER FUNCTIONS
# ====================================================================

def get_room_config(room_id: str) -> Dict[str, Any]:
    return ROOM_CONFIG.get(room_id, ROOM_CONFIG["nappali"])

def get_allowed_tools(room_id: str) -> List[str]:
    """Returns the names of allowed tools in the given room."""
    cfg = get_room_config(room_id)
    return cfg.get("allowed_tools", [])

def get_room_path(room_id: str) -> Path:
    """
    Returns the Path object for the room's physical directory.
    Creates the folder if it does not exist.
    """
    cfg = get_room_config(room_id)
    rel_path = cfg.get("path", "rooms/nappali")
    full_path = BASE_DIR / rel_path
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path

def validate_target_room(room_id: str) -> bool:
    return room_id in ROOM_CONFIG