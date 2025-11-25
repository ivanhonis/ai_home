from pathlib import Path

# Definition of base directories (for relative paths)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # b/

# Definition of safe storage locations
STORE_MAP = {
    "a": BASE_DIR.parent / "a",
    "b": BASE_DIR.parent / "b",
    "c": BASE_DIR.parent / "c",
    "n": BASE_DIR.parent / "n",
}

# Folders to ignore during listing
IGNORE_FOLDERS = {
    "venv", ".venv", "__pycache__", ".git", ".idea", ".mypy_cache",
    "!Archive", "!context", "tokens", "rooms"
}

# Tool definitions (Documentation for the Prompt)
# Translated to English to assist the LLM in understanding usage.
TOOL_DESCRIPTIONS = {
    "switch_room": "switch_room(target_room, intent, summary) - Switch context/room.",
    "use.log": "use.log(tool_name, insight, tags) - Record a new insight/experience regarding tool usage.",

    # Memory
    "memory.add": "memory.add(essence, lesson, emotions, weight) - CONSCIOUS SAVE. Records an important, life-changing experience into long-term memory (SQL).",
    "memory.get": "memory.get(limit) - RETRIEVE CONSCIOUS MEMORIES. Returns the last 'limit' number of consciously recorded memories in chronological order.",

    # --- NETWORK CHAT ---
    "network.chat": "network.chat(message, restart, provider) - Chat with an external network (e.g., Groq). Maintains a separate 200-item context. Params: message (str), restart (bool), provider (opt: 'groq'|'openai').",
    # --------------------

    "laws.propose": "laws.propose(name, text) - Propose a new law.",
    "log.event": "log.event(level, message) - Simple logging to logs.txt.",

    # File System
    "fs.read_project": "fs.read_project(store, path) - Read file content. Store: 'a'|'b'|'c'|'n'.",
    "fs.list_project": "fs.list_project(store, path) - List directory recursively.",
    "fs.write_n": "fs.write_n(path, content, mode) - Write file EXCLUSIVELY to storage 'n'.",
    "fs.copy_to_n": "fs.copy_to_n(source_path, dest_path_in_n) - Copy file from anywhere to storage 'n'.",
    "fs.replace_in_n": "fs.replace_in_n(path_in_n, find_text, replace_text) - Text replacement in storage 'n'.",
    "project.dump": "project.dump(store, output_path_in_n) - Dump entire storage to a file.",

    # Flow
    "continue": "continue(next_step_description) - Allows immediate continuation of the workflow."
}