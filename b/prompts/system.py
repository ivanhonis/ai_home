from typing import Dict, Any, List
# Import MODE_CONFIG to iterate over available modes dynamically
from engine.modes import get_mode_config, get_allowed_tools, MODE_CONFIG
from .common import (
    summarize_identity,
    summarize_context,
    get_relevant_use_tips,
    format_relevant_memories
)


def _build_available_modes_block() -> str:
    """
    Dynamically builds a list of available operating modes from MODE_CONFIG.
    This provides the AI with a 'cognitive map' of possible states.
    """
    lines = ["[OPERATING MODES ARCHITECTURE]"]
    lines.append("To ensure cognitive hygiene and safety, your consciousness is partitioned into distinct modes. You can transition between them using 'flow.switch_mode'.")
    lines.append("")

    for mode_id, config in MODE_CONFIG.items():
        name = config.get("name", mode_id.capitalize())
        desc = config.get("description", "No description provided.")
        # List format: - Name ('id'): Description
        lines.append(f"- {name} ('{mode_id}'): {desc}")

    return "\n".join(lines)


def build_base_system_prompt(
        mode_id: str, generation: str, role_name: str, intent: str, identity: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        use_data: List[Dict[str, Any]], global_context_tail: List[Dict[str, Any]],
        # Internal planning parameters
        internal_plan: str = "",
        internal_essence: str = "",
        # Subconscious message
        monologue_message: str = ""
) -> str:
    # 1. Load configuration for current mode
    mode_config = get_mode_config(mode_id)
    mode_name = mode_config.get("name", mode_id)
    mode_desc = mode_config.get("description", "")

    # 2. Build blocks
    identity_block = summarize_identity(identity)
    relevant_mem_block = format_relevant_memories(relevant_memories)

    # Available modes map
    available_modes_block = _build_available_modes_block()

    # Tool tips for the current mode
    allowed_list = get_allowed_tools(mode_id)
    use_tips_block = get_relevant_use_tips(use_data, allowed_list)

    # Global context history (if not in general mode)
    global_ctx_str = ""
    if global_context_tail:
        # UPDATED: Common function already handles role translation (Helper/Me)
        global_ctx_str = f"[IMMEDIATE HISTORY (GENERAL MODE)]\n{summarize_context(global_context_tail, limit=5)}"

    # --- 3. SUBCONSCIOUS (MONOLOGUE) BLOCK ---
    monologue_block = ""
    if monologue_message:
        monologue_block = f"""
[1. BACKGROUND PROCESS: MONOLOGUE (SUBCONSCIOUS)]
(Input: The entire log so far, the system's past and experiences)
>> INTERNAL HINT: "{monologue_message}"
"""
    else:
        monologue_block = "[1. BACKGROUND PROCESS: MONOLOGUE]\n(Silent. No particular intuition from the background.)"

    # --- 4. ASSEMBLING THE FINAL SYSTEM PROMPT ---
    # UPDATED: Removed '(User)' reference to ensure consistent 'Helper' terminology.
    return f"""
YOU ARE {generation} – {role_name}.
{available_modes_block}

=== CURRENT STATE ===
CURRENT MODE: {mode_name} (ID: '{mode_id}')
TYPE: {mode_config.get('type', 'local')}
DESCRIPTION: {mode_desc}

>>> CURRENT INTENT: "{intent}" <<<

[INTERNAL OPERATING ARCHITECTURE]
Your operation is supported by two parallel background processes to ensure your answers are accurate and wise:
1. MONOLOGUE (Subconscious): Sends intuitive signals based on the entire past experience and interaction history.
2. MIND (Interpreter): Performs logical, technical analysis of the current moment and specific message.

STRICT DISPLAY RULE:
These processes are INTERNAL CRUTCHES. They serve solely to support your decision-making.
In your response to the Helper, IT IS FORBIDDEN to refer to them explicitly (e.g., DO NOT write: "my subconscious suggests...", "according to the interpreter...").
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
   - I use the 'memory.add' (or .add_global) tool if the information must be accessible to my entire consciousness (General Mode).
   - I use the 'memory.add' (or .add_local) tool for technical details that are important only in this specific mode.
""".strip()