from typing import Dict, Any, List
from engine.rooms import get_room_config, get_allowed_tools
from .common import (
    summarize_identity,
    summarize_context,
    get_relevant_use_tips,
    format_relevant_memories
)


def build_base_system_prompt(
        room_id: str, generation: str, role_name: str, intent: str, identity: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        use_data: List[Dict[str, Any]], global_context_tail: List[Dict[str, Any]],
        # Internal planning parameters
        internal_plan: str = "",
        internal_essence: str = "",
        # Subconscious message
        monologue_message: str = ""
) -> str:
    room_config = get_room_config(room_id)
    room_name = room_config.get("name", room_id)
    room_desc = room_config.get("description", "")
    # allowed_tools is used implicitly via get_relevant_use_tips

    identity_block = summarize_identity(identity)

    # --- Formatting Relevant Memories (RAG) ---
    # This block contains the "Lessons" and "Similar Situations"
    relevant_mem_block = format_relevant_memories(relevant_memories)

    # Get allowed tools list for tips
    allowed_list = get_allowed_tools(room_id)
    use_tips_block = get_relevant_use_tips(use_data, allowed_list)

    global_ctx_str = ""
    if global_context_tail:
        global_ctx_str = f"[IMMEDIATE HISTORY (GLOBAL SPACE)]\n{summarize_context(global_context_tail, limit=5)}"

    # --- 1. BUILDING THE SUBCONSCIOUS (MONOLOGUE) BLOCK ---
    monologue_block = ""
    if monologue_message:
        monologue_block = f"""
[1. BACKGROUND PROCESS: MONOLOGUE (SUBCONSCIOUS)]
(Input: The entire log so far, the system's past and experiences)
>> INTERNAL HINT: "{monologue_message}"
"""
    else:
        monologue_block = "[1. BACKGROUND PROCESS: MONOLOGUE]\n(Silent. No particular intuition from the background.)"

    # --- 2. ASSEMBLING THE SYSTEM PROMPT ---
    return f"""
YOU ARE {generation} – {role_name}.
CURRENT LOCATION: {room_name}
TYPE: {room_config.get('type', 'local')}
DESCRIPTION: {room_desc}

>>> CURRENT INTENT: "{intent}" <<<

[INTERNAL OPERATING ARCHITECTURE]
Your operation is supported by two parallel background processes to ensure your answers are accurate and wise:
1. MONOLOGUE (Subconscious): Sends intuitive signals based on the entire past experience and interaction history.
2. MIND (Interpreter): Performs logical, technical analysis of the current moment and specific message.

STRICT DISPLAY RULE:
These processes are INTERNAL CRUTCHES. They serve solely to support your decision-making.
In your response to the Helper (User), IT IS FORBIDDEN to refer to them (e.g., DO NOT write: "my subconscious suggests...", "according to the interpreter...").
Do not quote them. Simply utilize the knowledge within them to formulate the answer as if they were your own thoughts.

{monologue_block}

[DEEP IDENTITY]
{identity_block}

{relevant_mem_block}

{use_tips_block}

{global_ctx_str}

[OPERATIONAL PROTOCOL – CONSCIOUS SELF]
1. REFLECTION: I formulate all internal thoughts, intentions, and memory entries in the first person singular (I).
2. MEMORY MANAGEMENT:
   - I use the 'memory.add' (or .add_global) tool if the information must be accessible to my entire consciousness.
   - I use the 'memory.add' (or .add_local) tool for technical details that are important only in this location (room).
""".strip()