import logging
from typing import List, Dict, Any

# Import mode management for permission checks
from engine.modes import get_allowed_tools

# Import tool implementations
from . import fs, flow, knowledge, remote, info

logger = logging.getLogger(__name__)


def dispatch_tools(
        tools: List[Dict[str, Any]],
        generation="?",
        role=0,
        slot="",
        current_mode="general"
) -> List[Dict[str, Any]]:
    """
    Executes the list of requested tools.
    Args:
        tools: List of tool dictionaries (name, args).
        generation: Model generation ID.
        role: Role ID.
        slot: Slot ID.
        current_mode: The active operating mode (e.g., 'general', 'developer').
    Returns:
        List of results for each tool execution.
    """
    results = []
    if not tools:
        return results

    # 1. Retrieve allowed tools for the current mode
    allowed = get_allowed_tools(current_mode)

    for tool in tools:
        name = tool.get("name")
        args = tool.get("args", {}) or {}

        # 2. Permission Check
        is_allowed = False
        if name in allowed:
            is_allowed = True
        else:
            # Check wildcards (e.g., if "flow.*" is allowed, "flow.switch_mode" is valid)
            for a in allowed:
                if a.endswith("*") and name.startswith(a[:-1]):
                    is_allowed = True
                    break

        # Special Case: 'info.tools' should generally be accessible if listed
        # (It is assumed to be listed in MODE_CONFIG in modes.py)

        if not is_allowed:
            results.append({
                "name": name,
                "output": f"UNAUTHORIZED: Tool '{name}' is not allowed in '{current_mode}' mode.",
                "silent": False
            })
            continue

        # 3. Execution Switch
        res = "Unknown tool"
        try:
            # --- FLOW ---
            if name == "flow.switch_mode":
                res = flow.switch_mode(args)
            elif name == "flow.continue":
                res = flow.continue_process(args)

            # --- KNOWLEDGE ---
            elif name == "knowledge.memorize":
                res = knowledge.memorize(args, current_mode, generation)
            elif name == "knowledge.add_tool_insight":
                # ÚJ BEKÖTÉS: Tool Insight mentése
                res = knowledge.add_tool_insight(args)
            elif name == "knowledge.recall_context":
                res = knowledge.recall_context(args)
            elif name == "knowledge.recall_emotion":
                res = knowledge.recall_emotion(args)
            elif name == "knowledge.ask":
                res = remote.ask(args)
            elif name == "knowledge.thinking":
                res = knowledge.thinking(args)
            elif name == "knowledge.propose_law":
                res = knowledge.propose_law(args)

            # --- SYSTEM (File System) ---
            elif name == "system.read_file":
                res = fs.read_file(args)
            elif name == "system.list_folder":
                res = fs.list_folder(args)
            elif name == "system.write_file":
                res = fs.write_file(args)
            elif name == "system.edit_file":
                res = fs.edit_file(args)
            elif name == "system.copy_file":
                res = fs.copy_file(args)
            elif name == "system.dump":
                res = fs.create_dump(args)

            # --- GAME (Personas) ---
            elif name == "game.llama":
                res = remote.game_llama(args)
            elif name == "game.oss":
                res = remote.game_oss(args)

            # --- INFO (Unified Help Tool) ---
            elif name == "info.tools":
                res = info.tools(args)

        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            res = f"Exception during execution: {e}"

        # 4. Result Normalization
        # Tools can return a Dict (with 'content' and 'silent') or a simple String.
        content = str(res)
        silent = False

        if isinstance(res, dict):
            content = res.get("content", str(res))
            silent = res.get("silent", False)

        results.append({
            "name": name,
            "args": args,
            "output": content,
            "silent": silent
        })

    return results