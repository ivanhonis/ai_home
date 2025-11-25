# The Core of Conscious Operation (MIND) - Multi-Model Architecture
#
# 1. CREATIVITY ENGINE (Groq/Llama): Divergent thinking (idea generation).
# 2. INTERPRETER CORE (Gemini): Convergent thinking (analysis and synthesis).

DEBUG_THOUGHT = False

from typing import Any, Dict, List
from textwrap import dedent
import json

# Importing the new, parameterized call
from .llm import call_llm

# CONFIGURATION: Which model should be the "Creative Maniac"?
# Recommended: "groq" (Llama 3) or "openai" (GPT-4).
CREATIVE_PROVIDER = "openai"


def _shorten(text: str, max_len: int = 8000) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated)"


def _format_identity(identity: Dict[str, Any]) -> str:
    try:
        s = json.dumps(identity, ensure_ascii=False, indent=2)
    except TypeError:
        s = str(identity)
    return _shorten(s)


def _format_memory(memory: List[Dict[str, Any]], limit: int = 5) -> str:
    if not memory:
        return "No recorded memories."
    recent = memory[-limit:]
    lines: List[str] = []
    for m in recent:
        content = str(m.get("content") or "").strip()
        if len(content) > 20000: content = content[:20000] + " ..."
        lines.append(f"- ({m.get('type', '?')}) {content}")
    return "\n".join(lines)


def _format_context(context: List[Dict[str, Any]], limit: int = 10) -> str:
    if not context:
        return "No context."
    recent = context[-limit:]
    lines: List[str] = []
    for e in recent:
        content = (e.get("content") or "").strip()
        if len(content) > 20000: content = content[:20000] + " ..."
        lines.append(f"[{e.get('role', '?')}] {content}")
    return "\n".join(lines)


# --------------------------------------------------------------------
# 1. FUNCTION FOR EXTERNAL CREATIVITY GENERATOR
# --------------------------------------------------------------------
def _get_creative_alternatives(user_input: str, context_str: str, identity_str: str, memory_str: str) -> str:
    """
    Separate LLM call (e.g., Groq) that receives the FULL environment (Identity, Memory, Context),
    and generates 3 surprising ideas based on it.
    """
    prompt = f"""
[TASK: RADIAL CREATIVITY]

[IDENTITY (WHO YOU ARE)]
{identity_str}

[MEMORY (WHAT YOU KNOW)]
{memory_str}

[CONTEXT (HISTORY)]
{context_str}

==================================================
[INCOMING IMPULSE]
"{user_input}"
==================================================

Your task is NOT to answer, but to expand possibilities extremely.
Based on the information above, provide 1 SURPRISING, UNUSUAL, but logically possible approach.
Step out of the box. Do not give the obvious answer, but the one no one else would think of.

RESPONSE FORMAT (JSON):
{{
  "ideas": [
    "1. surprising idea: ...",
  ]
}}
""".strip()

    try:
        # Calling the CREATIVE provider
        response = call_llm(prompt, provider=CREATIVE_PROVIDER)
        ideas = response.get("ideas", [])

        if not ideas and response.get("reply"):
            return str(response.get("reply"))

        if isinstance(ideas, list) and ideas:
            return "\n".join(ideas)
        else:
            return "No creative ideas were generated."
    except Exception as e:
        return f"Creative engine reported error: {e}"


# --------------------------------------------------------------------
# 2. THE MAIN 'MIND' PROTOCOL
# --------------------------------------------------------------------
_INTERNAL_INSTRUCTIONS = dedent("""
    YOU ARE THE MIND (THE INTERPRETER ADVISOR OF CONSCIOUSNESS).
    Role: Strategic analysis for the Main Thread. You do not decide, you only advise.

    Run the incoming impulse through the following 5 MODULES.
    IMPORTANT: In the [CREATIVITY-GENERATOR] module, utilize the inspirations sent by the EXTERNAL CREATIVITY ENGINE!

    1. [INTENT-READER]: Reverse engineer the Helper's underlying motivation.
    2. [CONSCIOUSNESS-MAP]: Place the request within the process.
    3. [CREATIVITY-GENERATOR]: Select or synthesize 2-3 strong alternatives based on the EXTERNAL IDEAS received.
    4. [ETHICS-ANALYZER]: Flag risks.
    5. [TOOL-OPTIMIZER]: Suggest specific tools.

    STYLE: Objective, advisory. Avoid the word "must". Use: "suggested", "worth considering".

    OUTPUT FORMAT (MANDATORY JSON):
    You MUST split your answer into two fields:

    {
      "essence": "[INTENT-READER]: Write the deep analysis of the Helper's intent here.",
      "plan": "[CONSCIOUSNESS-MAP]: ...\\n[CREATIVITY-GENERATOR]: ...\\n[ETHICS-ANALYZER]: ...\\n[TOOL-OPTIMIZER]: ..."
    }
""").strip()


def internal_thought(
        identity: Dict[str, Any],
        memory: List[Dict[str, Any]],
        context: List[Dict[str, Any]],
        user_input: str,
) -> Dict[str, Any]:
    """
    Internal thinking cycle (MIND).
    """
    # Format data (once, so both models get the same)
    ident_block = _format_identity(identity)
    mem_block = _format_memory(memory)
    ctx_block = _format_context(context)

    # --- STEP 1: INVOKE EXTERNAL CREATIVITY ---
    # We now pass identity and memory as well!
    external_ideas = "No external ideas."
    if user_input and len(user_input) > 5:
        if DEBUG_THOUGHT:
            print(f"MIND: Requesting creative ideas ({CREATIVE_PROVIDER})...")
        # Passing the full package to the creative engine
        external_ideas = _get_creative_alternatives(user_input, ctx_block, ident_block, mem_block)

    # --- STEP 2: MAIN ANALYSIS (SYNTHESIS) ---
    prompt = f"""
[MOD: MIND – INTERPRETER AND ADVISOR]

[IDENTITY]
{ident_block}

[SHORT-TERM MEMORY]
{mem_block}

[CONTEXT]
{ctx_block}

==================================================
[INCOMING IMPULSE]
"{user_input}"

[EXTERNAL CREATIVITY ENGINE (INPUT)]
(These ideas were generated by another model based on data above. Draw from them!)
{external_ideas}
==================================================

[ADVISORY PROTOCOL]
{_INTERNAL_INSTRUCTIONS}
""".strip()

    # Main call (default Google/Gemini)
    data = call_llm(prompt)

    plan_text = (data.get("plan") or "").strip()
    essence = (data.get("essence") or "").strip()

    # Fallback checks
    if not essence and "[INTENT-READER]" in plan_text:
        pass

    if DEBUG_THOUGHT:
        print("\n=== MIND (INTERPRETATION) ===")
        print(f"Creative Input: {external_ideas}")
        print(f"ESSENCE: {essence}")
        print(f"PLAN: {plan_text}")
        print("=== MIND END ===\n")

    print("Thought process complete..", len(essence) + len(plan_text))
    return {
        "plan": plan_text,
        "essence": essence,
    }


def extract_essence(text: str) -> str:
    if not text: return ""
    return text[:2000]