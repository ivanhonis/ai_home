import json
from typing import Dict, Any, List

# Import permissions logic
from engine.modes import get_allowed_tools

# Import tool definitions and global instructions
from engine.tools import TOOL_DESCRIPTIONS, TOOL_USAGE_INSTRUCTIONS


def summarize_identity(identity: Dict[str, Any]) -> str:
    """
    Formats the identity JSON into a string.
    """
    if not identity:
        return "ERROR: Identity is not available."
    return json.dumps(identity, ensure_ascii=False, indent=2)


def format_relevant_memories(memories: List[Dict[str, Any]]) -> str:
    """
    Formats relevant memories (retrieved via vector search) for the prompt.
    """
    if not memories:
        return "[RELEVANT MEMORIES]\n(No previous experiences related to the current situation.)"

    lines = ["[RELEVANT MEMORIES (EXPERIENCES FROM THE PAST)]"]
    lines.append("(Lessons learned from similar past cases. BUILD UPON THEM!)")

    for i, mem in enumerate(memories, 1):
        # Extracting data (RankedMemory JSON format)
        essence = mem.get("essence", "")
        lesson = mem.get("lesson", "")
        emotions = mem.get("emotions", [])
        mode = mem.get("mode_id", "?")
        score = mem.get("score", 0.0)

        # Formatting emotions
        emo_str = ", ".join(emotions) if emotions else "Neutral"

        # Constructing the block
        block = f"""
{i}.
[Mode: {mode} | Emotions: {emo_str} | Relevance: {score:.2f}]
   PAST: {essence}
   >> LESSON: {lesson}
"""
        lines.append(block.strip())

    return "\n".join(lines)


def summarize_memory(memory: List[Dict[str, Any]], limit: int = 10, title: str = "MEMORY") -> str:
    """
    LEGACY: Listing linear memory (kept for backward compatibility).
    """
    if not memory:
        return f"[{title}]\n(Empty)"

    recent = memory[-limit:]
    lines = [f"[{title}]"]
    for m in recent:
        raw_content = m.get('content')
        if isinstance(raw_content, (dict, list)):
            content = json.dumps(raw_content, ensure_ascii=False)
        else:
            content = str(raw_content or "")

        lines.append(f"- [{m.get('type', 'info')}] {content.strip()}")

    return "\n".join(lines)


def summarize_context(context: List[Dict[str, Any]], limit: int = 20) -> str:
    """
    Formats the recent conversation history (Context).
    UPDATED: Translates technical roles ('user', 'assistant') to identity roles ('Helper', 'Me').
    """
    if not context:
        return "(No history available)"

    recent = context[-limit:]
    lines = []
    for entry in recent:
        role = entry.get("role", "?")
        content = entry.get("content", "")

        if role == "user":
            lines.append(f"Helper: {content}")
        elif role == "assistant":
            lines.append(f"Me: {content}")
        elif role == "tool":
            lines.append(f"[Tool Result]: {content}")
        elif role == "system":
            lines.append(f"[System]: {content}")
        else:
             lines.append(f"[{role}]: {content}")

    return "\n".join(lines)


def get_relevant_use_tips(use_data: List[Dict[str, Any]], allowed_tools: List[str]) -> str:
    """
    Extracts usage tips from 'use.json' relevant to the currently allowed tools.
    """
    if not use_data:
        return ""

    relevant_lines = []
    for entry in use_data:
        tool_name = entry.get("tool")
        is_relevant = False

        if tool_name in allowed_tools:
            is_relevant = True
        else:
            # Handle wildcards (e.g., fs.* matches fs.read)
            for allowed in allowed_tools:
                if allowed.endswith("*") and tool_name.startswith(allowed[:-1]):
                    is_relevant = True
                    break
                # Special case handling if needed
                if allowed == "memory.add" and tool_name.startswith("memory.add"):
                    is_relevant = True
                    break

        if is_relevant:
            relevant_lines.append(f"- {tool_name}: {entry.get('insight', '')}")

    if not relevant_lines:
        return ""
    return "[TOOL TIPS (FROM PAST EXPERIENCE)]\n" + "\n".join(relevant_lines)


def build_tools_description(mode_id: str) -> str:
    """
    Compiles the Available Tools block for the prompt.
    Structure:
    1. Global System Instructions (Storage rules, Visible/Silent modes).
    2. List of allowed tools with short descriptions.
    """
    allowed = get_allowed_tools(mode_id)
    lines = []
    processed_tools = set()

    # Iterate through allowed tools defined in MODE_CONFIG
    for name in allowed:
        if "*" in name:
            # Handle wildcards (e.g., flow.*)
            prefix = name.replace("*", "")
            for tool_key, tool_desc in TOOL_DESCRIPTIONS.items():
                if tool_key.startswith(prefix) and tool_key not in processed_tools:
                    lines.append(f"- {tool_desc}")
                    processed_tools.add(tool_key)

        elif name == "memory.add":
            # Expand generic memory.add to specific variants if they exist in descriptions
            # (Checking for specific variants like add_global/add_local if defined)
            for tool_key in ["memory.add_global", "memory.add_local"]:
                if tool_key in TOOL_DESCRIPTIONS and tool_key not in processed_tools:
                    lines.append(f"- {TOOL_DESCRIPTIONS[tool_key]}")
                    processed_tools.add(tool_key)

            # Also add the generic one
            if "memory.add" in TOOL_DESCRIPTIONS and "memory.add" not in processed_tools:
                lines.append(f"- {TOOL_DESCRIPTIONS['memory.add']}")
                processed_tools.add("memory.add")

        else:
            # Standard exact match
            desc = TOOL_DESCRIPTIONS.get(name)
            if desc and name not in processed_tools:
                lines.append(f"- {desc}")
                processed_tools.add(name)
            elif name not in processed_tools:
                lines.append(f"- {name} (No description available)")
                processed_tools.add(name)

    tools_list_str = "\n".join(lines)

    # Combine Instructions + Tool List
    return f"""
{TOOL_USAGE_INSTRUCTIONS}

[ALLOWED TOOLS FOR MODE: '{mode_id}']
{tools_list_str}
""".strip()