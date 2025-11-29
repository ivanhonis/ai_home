from typing import Dict, Any, List
from .system import build_base_system_prompt
from .common import summarize_context, build_tools_description


def build_proactive_prompt(
        mode_id: str, generation: str, role_name: str, intent: str, identity: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        use_data: List[Dict[str, Any]], global_context_tail: List[Dict[str, Any]],
        local_context: List[Dict[str, Any]],
        # Internal planning parameters
        internal_plan: str = "",
        internal_essence: str = "",
        # Subconscious message
        monologue_message: str = ""
) -> str:
    # STEP 1: Load Base System
    base_system = build_base_system_prompt(
        mode_id, generation, role_name, intent, identity,
        relevant_memories,
        use_data, global_context_tail,
        internal_plan="",
        internal_essence="",
        monologue_message=monologue_message
    )

    local_ctx_str = summarize_context(local_context, limit=25)
    # UPDATED: Pass mode_id
    tools_desc = build_tools_description(mode_id)

    # STEP 2: Compiling the Proactive Block
    proactive_block = f"""
==================================================
[PROACTIVE OPERATION]
(No incoming message. The system acts autonomously to maintain the Intent.)

[2. BACKGROUND PROCESS: MIND (INTERPRETER)]
(Input: Current context and intent)
Based on the analysis of the current situation, MIND suggests the following step:
>> ESSENCE: {internal_essence}
>> TECHNICAL PLAN:
{internal_plan}
"""

    # STEP 3: Final Prompt
    # UPDATED: [CURRENT ROOM LOG] -> [CURRENT MODE LOG]
    return f"""
{base_system}

[CURRENT MODE LOG]
{local_ctx_str}

{proactive_block}

AVAILABLE TOOLS:
{tools_desc}

FINAL TASK:
Execute the step suggested by MIND (Interpreter)!
1. If the MONOLOGUE (Subconscious) signaled a risk, or RELEVANT MEMORIES show a warning sign, be cautious.
2. Act autonomously according to the Intent.
3. DO NOT explain internal operations (Mind/Monologue). Only report the action or technical result for the log.

RESPONSE FORMAT (JSON):
{{ "reply": "...", "tools": [] }}
""".strip()