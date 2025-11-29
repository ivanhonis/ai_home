from typing import Dict, Any
# Import data from config
from engine.tools.config import (
    TOOL_DESCRIPTIONS,
    TOOL_DESCRIPTIONS_DETAILS,
    TOOL_USAGE_INSTRUCTIONS
)


def tools(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Universal Help Tool implementation.
    Handles: info.tools(target="...")

    Logic:
    1. If target="all" -> Returns global instructions + summary list of all tools.
    2. If target="tool_name" -> Returns detailed manual for that specific tool.
    3. If target="prefix" -> Returns detailed manuals for all tools starting with that prefix.
    """
    # 1. Extract parameter (supporting legacy 'group' key as fallback)
    target = args.get("target") or args.get("group") or "all"
    target = str(target).lower().strip()

    lines = []

    # 2. HEADER: Global Instructions (Always visible to reinforce rules)
    lines.append(TOOL_USAGE_INSTRUCTIONS.strip())
    lines.append("\n" + ("=" * 60) + "\n")

    # 3. DISPATCH LOGIC based on user request

    # A) "all" -> Summary List
    if target == "all":
        lines.append("[AVAILABLE TOOLS - SUMMARY LIST]")
        lines.append("(For detailed params, use: info.tools(target='tool_name'))\n")

        # List in alphabetical order
        for key in sorted(TOOL_DESCRIPTIONS.keys()):
            desc = TOOL_DESCRIPTIONS[key]
            lines.append(f"- {desc}")

    # B) Specific Tool (Exact match in DETAILS)
    elif target in TOOL_DESCRIPTIONS_DETAILS:
        lines.append(f"[DETAILED MANUAL: {target.upper()}]")
        lines.append(TOOL_DESCRIPTIONS_DETAILS[target].strip())

    # C) Group Search (Prefix match, e.g., "system")
    else:
        # Append dot if missing to avoid partial matches (e.g. "sys" matching "system")
        # However, we want "system" to match "system.read", so we check starts_with.
        prefix = target if target.endswith(".") else f"{target}."

        matches = [k for k in TOOL_DESCRIPTIONS_DETAILS.keys() if k.startswith(prefix)]

        if matches:
            lines.append(f"[MANUAL FOR GROUP: '{target.upper()}']")
            for key in sorted(matches):
                lines.append(f"\n--- TOOL: {key} ---")
                lines.append(TOOL_DESCRIPTIONS_DETAILS[key].strip())
        else:
            # ERROR HANDLING
            return {
                "content": f"Help Error: No tool or group found for '{target}'.\n"
                           f"Try 'all', 'system', 'flow', 'knowledge', or a specific tool name.",
                "silent": False
            }

    # 4. Construct Response
    return {
        "content": "\n".join(lines),
        "silent": False
    }


# Aliases for backward compatibility (if needed by older calls)
tools_general = tools
tools_group = tools