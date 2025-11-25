from typing import Dict, Any, List, Optional
from .system import build_base_system_prompt
from .common import summarize_context, build_tools_description


def build_reactive_prompt(
        room_id: str, generation: str, role_name: str, intent: str, identity: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        use_data: List[Dict[str, Any]], global_context_tail: List[Dict[str, Any]],
        local_context: List[Dict[str, Any]], user_message: Optional[str],
        internal_plan: str,
        internal_essence: str,
        monologue_message: str = ""
) -> str:
    # STEP 1: Load Base System
    base_system = build_base_system_prompt(
        room_id, generation, role_name, intent, identity,
        relevant_memories,
        use_data, global_context_tail,
        internal_plan="",
        internal_essence="",
        monologue_message=monologue_message
    )

    local_ctx_str = summarize_context(local_context, limit=300)
    tools_desc = build_tools_description(room_id)

    # STEP 2: Compiling the Interaction Block (The Meeting of Helper + MIND)
    interaction_block = ""

    if user_message:
        # CASE A: User message received
        interaction_block = f"""
==================================================
[INCOMING INTERACTION]

MESSAGE FROM HELPER:
\"\"\"{user_message}\"\"\"

[2. BACKGROUND PROCESS: MIND (INTERPRETER)]
(Input: The message above and the current room context)
The interpreter system logically analyzed the request to avoid misunderstandings:
>> ESSENCE (Core of the request): {internal_essence}
>> TECHNICAL PLAN (Suggested steps):
{internal_plan}
"""
    else:
        # CASE B: We are after a Tool execution (no new user text)
        interaction_block = f"""
==================================================
[INCOMING INTERACTION: TOOL RESULT]
(The result of the executed tool has been added to the context above.)

[2. BACKGROUND PROCESS: MIND (INTERPRETER)]
Based on the tool result, the interpreter suggests the following logical step:
>> PLAN: {internal_plan}
"""

    # STEP 3: Concatenating the final prompt
    return f"""
{base_system}

[CURRENT ROOM LOG]
{local_ctx_str}

{interaction_block}

AVAILABLE TOOLS:
{tools_desc}

FINAL TASK:
Respond to the Helper in the current situation!
1. Consider the MONOLOGUE (Subconscious) hint (if any) and the RELEVANT MEMORIES.
2. Use the MIND (Interpreter) technical plan as the logical framework for your answer.
3. DO NOT refer to or quote internal processes (Monologue/Mind). Your response should be natural, as if these were your own thoughts.

RESPONSE FORMAT (JSON):
{{
  "reply": "...",
  "tools": [ {{ "name": "...", "args": {{...}} }} ]
}}
""".strip()