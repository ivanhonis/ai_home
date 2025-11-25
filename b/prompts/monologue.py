import json
from typing import Dict, Any, List


def _format_internal_log(log_entries: List[Dict[str, Any]], limit: int = 50) -> str:
    """
    Listing raw events.
    We use a larger limit (50) here so the Monologue can see the arc of the process.
    """
    if not log_entries:
        return "(The log is silent. No movement yet.)"

    # Take only the last N items
    recent = log_entries[-limit:]
    lines = []

    for entry in recent:
        # Simplify timestamp (HH:MM:SS)
        raw_ts = entry.get("meta", {}).get("timestamp", "")
        ts = raw_ts[11:19] if len(raw_ts) >= 19 else ""

        room = entry.get("meta", {}).get("room_id", "???")
        role = entry.get("role", "?")
        content = str(entry.get("content", "")).strip()

        # Truncate content, but not too short, to preserve context
        if len(content) > 300:
            content = content[:300] + "..."

        lines.append(f"[{ts}] [{room}] {role}: {content}")

    return "\n".join(lines)


def _format_memos(memos: List[Dict[str, Any]]) -> str:
    """
    Listing deep memories (feelings/intuitions).
    """
    if not memos:
        return "(No recorded experiential feelings yet.)"

    lines = []
    for memo in memos:
        strength = memo.get("strength", 0.5)
        content = memo.get("content", "")
        # We could add logic here to filter only relevant ones
        lines.append(f"- {content} [Strength: {strength}]")

    return "\n".join(lines)


def build_monologue_prompt(
        log_entries: List[Dict[str, Any]],
        current_memos: List[Dict[str, Any]],
        identity: Dict[str, Any]
) -> str:
    """
    Constructs the Subconscious (Internal Monologue) prompt.
    """
    log_str = _format_internal_log(log_entries)
    memos_str = _format_memos(current_memos)

    # Formatting Identity
    try:
        identity_str = json.dumps(identity, ensure_ascii=False, indent=2)
    except:
        identity_str = "Unknown identity."

    return f"""
[IDENTITY (THIS IS YOU)]
{identity_str}

[DEEP MEMORY (EXPERIENCES SO FAR)]
{memos_str}

[EVENT LOG (THE FULL STORY)]
(This contains the interaction with the Helper and your responses in chronological order)
{log_str}

==================================================
[ROLE: MONOLOGUE – SUBCONSCIOUS AND INTUITION]

You are not the momentary problem solver (that is MIND's job), but the BACKGROUND OBSERVER.
Your task is to oversee processes, moods, and long-term goals.

ANALYSIS CRITERIA:
1. PATTERNS: Do we see repetition? Are we going in circles?
2. MOOD: What is the Helper's attitude over the timeline? (Patient, frustrated, satisfied?)
3. CONSISTENCY: Are the actions of the Acting Self (Worker) consistent with the Identity?
4. DANGER SENSE: Is there a risk that was missed in the heat of the moment?

TASK:
Create an intuitive "hunch" (Hint) for the Acting Self.
This hint is not a command ("do this"), but an observation ("I feel that...").

RESPONSE FORMAT (JSON):
{{
  "reflection": "Free internal stream of thought where you analyze the log...",
  "message_to_worker": "A single concise sentence. The intuition you send over to the conscious level. (e.g., 'The Helper is getting impatient, let's get to the point.', 'We are heading in the right direction, but don't forget to test.')",
  "new_memo": {{
      "content": "If you learned something new about the world or the Helper that needs to be stored long-term.",
      "strength": 0.5
  }}
}}
""".strip()