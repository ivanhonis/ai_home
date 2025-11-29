# MODE SWITCH TRANSITIONS (CONSCIOUS BRIDGE LOGIC)
#
# These SYSTEM MESSAGES (system/system_event) are added to the context
# as a result of the switch_mode call to stabilize the state.

def get_transition_message(key: str, intent: str, summary: str) -> str:
    """
    Returns the requested transition message substituted with incoming data.
    UPDATED: Spatial metaphors replaced with Functional/State metaphors.
    """

    # 1. General -> Local (To General Context)
    M1_EXIT = "[SYSTEM LOG] Global attention SUSPENDED. Focus SHIFTED to specialized context. Trigger intent: \"{intent}\"."

    # 2. General -> Local (To Local Context)
    M2_ENTRY = "[SYSTEM LOG] Specialized session STARTED. Context ISOLATED. Objective defined as: \"{intent}\"."

    # 3. Local -> General (To Local Context)
    M3_EXIT = "[SYSTEM LOG] Specialized session CLOSED. Outcomes LOGGED. Returning control to Global Context."

    # 4. Local -> General (To General Context)
    M4_ENTRY = "[SYSTEM LOG] Global Context RESUMED. Workflow CONTINUED after specialized task. Summary of interim events: {summary}."

    MESSAGES = {
        "exit_general": M1_EXIT,
        "entry_local": M2_ENTRY,
        "exit_local": M3_EXIT,
        "entry_general": M4_ENTRY,
    }

    template = MESSAGES.get(key, f"ERROR: Unknown transition: {key}")

    # Formatting the string
    return template.format(
        intent=intent.strip() or "Not specified",
        summary=summary.strip() or "No summary"
    )