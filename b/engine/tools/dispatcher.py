import logging
from typing import List, Dict, Any

# Engine modules
from engine.rooms import get_allowed_tools

# Local tool modules
from . import fs, flow, knowledge, remote

logger = logging.getLogger(__name__)


def dispatch_tools(
        tools: List[Dict[str, Any]],
        generation="E?",
        role=0,
        slot="",
        current_room="nappali"
) -> List[Dict[str, Any]]:
    """
    Central Tool Dispatcher (Router).
    1. Checks permissions for the current room.
    2. Selects the appropriate module and function.
    3. Executes and standardizes output.
    """
    results = []
    if not tools:
        return results

    allowed_tool_names = get_allowed_tools(current_room)

    for tool in tools:
        name = tool.get("name")
        args = tool.get("args", {}) or {}

        # logger.debug(f"Running tool: {name} ({current_room})")

        # --- 1. PERMISSION CHECK ---
        is_allowed = False
        if name in allowed_tool_names:
            is_allowed = True
        else:
            # Wildcard check (e.g., "fs.*" or "network.*")
            for allowed in allowed_tool_names:
                if allowed.endswith("*") and name.startswith(allowed[:-1]):
                    is_allowed = True
                    break

        if not is_allowed:
            logger.warning(f"Unauthorized tool attempt: {name} in {current_room}")
            results.append({
                "name": name,
                "args": args,
                "output": f"UNAUTHORIZED: '{name}' is forbidden here ({current_room}).",
                "silent": False
            })
            continue

        # --- 2. EXECUTION (ROUTING) ---
        output_content = None
        is_silent = False

        try:
            raw_result = None

            # --- MEMORY AND KNOWLEDGE ---
            if name == "memory.add":
                raw_result = knowledge.memory_add(args, current_room, generation)
            elif name == "memory.get":
                raw_result = knowledge.memory_get(args)
            elif name == "use.log":
                raw_result = knowledge.use_log(args)
            elif name == "laws.propose":
                raw_result = knowledge.laws_propose(args)
            elif name == "log.event":
                raw_result = knowledge.log_event(args)

            # --- EXTERNAL COMMUNICATION ---
            elif name == "network.chat":
                raw_result = remote.network_chat(args)

            # --- FLOW CONTROL ---
            elif name == "switch_room":
                raw_result = flow.switch_room(args)
            elif name == "continue":
                raw_result = flow.continue_process(args)

            # --- FILE SYSTEM (FS) ---
            elif name == "fs.read_project":
                raw_result = fs.read_project(args)
            elif name == "fs.list_project":
                raw_result = fs.list_project(args)
            elif name == "fs.write_n":
                raw_result = fs.write_n(args)
            elif name == "fs.copy_to_n":
                raw_result = fs.copy_to_n(args)
            elif name == "fs.replace_in_n":
                raw_result = fs.replace_in_n(args)
            elif name == "project.dump":
                raw_result = fs.project_dump(args)

            else:
                raw_result = f"Unknown tool: {name}"

            # --- 3. OUTPUT STANDARDIZATION ---
            if isinstance(raw_result, dict) and "content" in raw_result:
                # New dictionary type return
                output_content = raw_result["content"]
                is_silent = raw_result.get("silent", False)
            else:
                # Old string type return -> Always "loud"
                output_content = str(raw_result)
                is_silent = False

        except Exception as e:
            output_content = f"Critical error during tool execution: {e}"
            is_silent = False
            logger.error(f"Tool error ({name}): {e}", exc_info=True)

        results.append({
            "name": name,
            "args": args,
            "output": output_content,
            "silent": is_silent
        })

    return results