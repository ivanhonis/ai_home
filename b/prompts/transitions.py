# ROOM SWITCH TRANSITIONS (CONSCIOUS BRIDGE LOGIC)
#
# These SYSTEM MESSAGES (system/system_event) are added to the context
# as a result of the switch_room call to stabilize the state.

def get_transition_message(key: str, intent: str, summary: str) -> str:
    """
    Returns the requested transition message substituted with incoming data.
    """

    # 1. Living Room -> Lower Room (To Living Room Context)
    M1_EXIT = "[CONTINUING] Started internal task with intent: \"{intent}\". I will return when finished."

    # 2. Living Room -> Lower Room (To Lower Room Context)
    M2_ENTRY = "[PRESENT] I am here again. Immediate task: \"{intent}\". (Previous conclusion: {summary})"

    # 3. Lower Room -> Living Room (To Lower Room Context)
    M3_EXIT = "[COMPLETED] I closed the internal task. Conclusion passed to the Conscious Bridge, waiting to return."

    # 4. Lower Room -> Living Room (To Living Room Context)
    M4_ENTRY = "[RETURN] I have returned. Summary of work done: {summary}. I continue working here."

    MESSAGES = {
        "exit_global": M1_EXIT,
        "entry_local": M2_ENTRY,
        "exit_local": M3_EXIT,
        "entry_global": M4_ENTRY,
    }

    template = MESSAGES.get(key, f"ERROR: Unknown transition: {key}")

    # Formatting the string
    return template.format(
        intent=intent.strip() or "Not specified",
        summary=summary.strip() or "No summary"
    )