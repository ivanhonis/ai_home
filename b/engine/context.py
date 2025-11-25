import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime

# Room path handling
from .rooms import get_room_path

# Keep maximum this many messages in room context
MAX_CONTEXT_ITEMS = 1000

# --- NEW: Subconscious Log Settings ---
# This file will be in the project root (b/), not in rooms
INTERNAL_LOG_FILENAME = "log_for_internal.json"
# Subconscious sees this much history (to see process, not just the moment)
MAX_INTERNAL_LOG_ITEMS = 50

Role = Literal["user", "assistant", "tool", "system"]
EntryType = Literal[
    "message", "tool_call", "tool_result", "system_note", "system_event"]


def _now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def _get_context_file(room_id: str) -> Path:
    """
    Returns the path to the context.json file of the given room.
    Automatically handles folder differences using the rooms module.
    """
    room_dir = get_room_path(room_id)
    return room_dir / "context.json"


# --- NEW: Helper to access internal log ---
def _get_internal_log_file() -> Path:
    """
    Returns the global 'log_for_internal.json' path.
    The file is in the 'b/' directory (parent of the parent of this file).
    """
    # context.py -> engine/ -> b/
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / INTERNAL_LOG_FILENAME


def load_context(room_id: str) -> List[Dict[str, Any]]:
    """
    Loads context for a specific room.
    Returns empty list if file does not exist or is corrupted.
    """
    file_path = _get_context_file(room_id)

    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            # Return only the last N items to save memory
            return data[-MAX_CONTEXT_ITEMS:]

        return []
    except Exception:
        # Start clean if file is corrupted so the system doesn't crash
        return []


def save_context(room_id: str, context: List[Dict[str, Any]]) -> None:
    """
    Saves context for a specific room.
    Always trim the list to MAX_CONTEXT_ITEMS.
    """
    trimmed = context[-MAX_CONTEXT_ITEMS:]
    file_path = _get_context_file(room_id)

    # Ensure folder exists (get_room_path should do this, but double check)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


# --- NEW: Writing to Subconscious Log ---
def _append_to_internal_log(entry: Dict[str, Any], room_id: str) -> None:
    """
    Appends an event to the global internal log.
    Augments the entry with 'room_id' so the subconscious knows where it happened.
    """
    log_path = _get_internal_log_file()

    # Load
    data = []
    if log_path.exists():
        try:
            with log_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = []

    # Create copy of entry to avoid modifying original
    log_entry = entry.copy()
    # Extend metadata with location
    if "meta" not in log_entry:
        log_entry["meta"] = {}
    log_entry["meta"]["room_id"] = room_id

    data.append(log_entry)

    # Trim (Rolling Buffer)
    if len(data) > MAX_INTERNAL_LOG_ITEMS:
        data = data[-MAX_INTERNAL_LOG_ITEMS:]

    # Save
    try:
        with log_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"ERROR: Failed to write internal log: {e}")


def make_entry(
        role: Role,
        entry_type: EntryType,
        content: str,
        meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a standard context entry (message).
    """
    return {
        "role": role,
        "type": entry_type,
        "content": content,
        "meta": {
            **(meta or {}),
            "timestamp": _now_iso(),
        },
    }


def append_entry(
        room_id: str,
        context: List[Dict[str, Any]],
        entry: Dict[str, Any],
        auto_save: bool = True,
) -> List[Dict[str, Any]]:
    """
    Appends a new item to the context of a specific room.
    Returns the updated list.
    """
    context.append(entry)

    # FIFO cleanup if limit exceeded
    if len(context) > MAX_CONTEXT_ITEMS:
        overflow = len(context) - MAX_CONTEXT_ITEMS
        if overflow > 0:
            del context[0:overflow]

    if auto_save:
        save_context(room_id, context)

    # --- NEW: Automatic logging for the Subconscious ---
    # Everything entering the context (User msg, AI reply, Tool result)
    # also goes to the internal log so the 3rd thread can see it.
    _append_to_internal_log(entry, room_id)

    return context


def add_system_event(room_id: str, content: str, auto_save: bool = True) -> None:
    """
    NEW: Injects a system message (system/system_event) into the context.
    """
    # Loading Living Room (global) context is required for the full list
    context = load_context(room_id)

    entry = make_entry(
        role="system",
        entry_type="system_event",
        content=content
    )

    # Use existing append_entry logic (cleanup and save)
    # This now automatically writes to log_for_internal.json too!
    append_entry(room_id, context, entry, auto_save=auto_save)