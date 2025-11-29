from pathlib import Path
# Import Single Source of Truth
from engine.constants import ALLOWED_EMOTIONS

# Definition of base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # b/

# Helper to format the list for the prompt string (Global visibility)
_emotions_formatted = ", ".join([f'"{e}"' for e in ALLOWED_EMOTIONS])

# ====================================================================
# 1. GLOBAL SYSTEM INSTRUCTIONS (Always visible in context)
# ====================================================================
TOOL_USAGE_INSTRUCTIONS = f"""
[SYSTEM CONCEPTS: TOOL OUTPUTS & STORAGE]

1. TOOL EXECUTION MODES:
   - [VISIBLE]: Standard mode. The output is added to the conversation history. You SEE it and MUST react to it.
   - [SILENT]: Background operation. The output is logged internaly but NOT shown to you immediately. Do not wait for it.

2. FILE SYSTEM STORES (Virtual Drives):
   You interact with protected virtual stores, not absolute paths.
   - 'a', 'c': READ-ONLY (Archive/Backup).
   - 'b': READ-ONLY (Current Source Code). You CANNOT write here.
   - 'n': READ/WRITE (Incubator). ALL code modifications and new features MUST go here.
   - 'temp': READ/WRITE (Temporary scratchpad).

3. EMOTION TAXONOMY (For Memory & Recall):
   When using 'knowledge.recall_emotion' or creating memories, YOU MUST USE THESE TAGS:
   [ {_emotions_formatted} ]
   
4. MODE SWITCHING & SUMMARIES (CRITICAL):
   When using 'flow.switch_mode', the 'summary' parameter is the ONLY memory the next state will have of this session.
   - TERMINOLOGY: Always use "Helper" (not "User").
   - CONTENT: Do NOT write "Helper asked to switch".
     INSTEAD, summarize the actual context.
"""

# ====================================================================
# 2. SHORT DESCRIPTIONS (Included in every prompt)
# ====================================================================
TOOL_DESCRIPTIONS = {
    # --- FLOW ---
    "flow.switch_mode": """
    SIGNATURE: flow.switch_mode(target_mode: str, intent: str, summary: str)
    TYPE: [VISIBLE]
    DESCRIPTION: Switches the operating mode (context).
    PARAMS:
      - target_mode: ID from config ('general', 'developer', 'analyst').
      - intent: The specific GOAL to be achieved in the NEW mode.
      - summary: A CONCISE RECAP of the interactions in the CURRENT mode.
          IMPORTANT RULES for Summary:
          1. TERMINOLOGY: Refer to the human as "Helper", NOT "User".
          2. CONTENT: Do NOT just say "Helper asked to switch". 
             Instead, summarize the actual work done or discussed (e.g., "Discussed RPG mechanics, Helper suggested a dragon character").
             This ensures the next mode understands what happened previously.
    SIDE EFFECT: Triggers system events and prompt reconfiguration.
    """,

    "flow.continue": "flow.continue(next_step) - [VISIBLE] Signal to continue process immediately.",

    # --- KNOWLEDGE ---
    "knowledge.memorize": "knowledge.memorize(essence, lesson, emotions, weight) - [SILENT] Save to Vector DB.",
    "knowledge.add_tool_insight": "knowledge.add_tool_insight(target_tool, insight) - [SILENT] Save a best practice usage tip for a specific tool.",
    "knowledge.recall_context": "knowledge.recall_context(query) - [VISIBLE] Search memories by topic.",
    "knowledge.recall_emotion": "knowledge.recall_emotion(emotions) - [VISIBLE] Search memories by emotion tags (See Taxonomy above).",
    "knowledge.ask": "knowledge.ask(question, restart) - [VISIBLE] Ask external network (Google/GPT).",
    "knowledge.thinking": "knowledge.thinking(context) - [SILENT] Trigger internal reflection.",
    "knowledge.propose_law": "knowledge.propose_law(name, text) - [SILENT] Propose new internal law.",

    # --- SYSTEM (FS) ---
    "system.read_file": "system.read_file(store, path) - [VISIBLE] Read file content.",
    "system.list_folder": "system.list_folder(store, path) - [VISIBLE] List directory.",
    "system.write_file": "system.write_file(store, path, content) - [VISIBLE] Write file. ALLOWED: 'n', 'temp'. FORBIDDEN: 'b'.",
    "system.edit_file": "system.edit_file(store, path, find, replace) - [VISIBLE] Replace text. ALLOWED: 'n', 'temp'.",
    "system.copy_file": "system.copy_file(from_store, from_path, to_store, to_path) - [VISIBLE] Copy file.",
    "system.dump": "system.dump(target_store, filename) - [VISIBLE] Dump store to 'temp'.",

    # --- GAME ---
    "game.llama": "game.llama(message, restart) - [VISIBLE] Chat with 'Llama' persona.",
    "game.oss": "game.oss(message, restart) - [VISIBLE] Chat with 'OSS' persona.",

    # --- INFO ---
    "info.tools": "info.tools(target) - [VISIBLE] Get help. target='all', 'system', or tool name."
}

# ====================================================================
# 3. DETAILED MANUAL (Returned by info.tools)
# ====================================================================
TOOL_DESCRIPTIONS_DETAILS = {
    # --- FLOW ---
    "flow.switch_mode": """
    SIGNATURE: flow.switch_mode(target_mode: str, intent: str, summary: str)
    TYPE: [VISIBLE]
    DESCRIPTION: Switches the operating mode (context).
    PARAMS:
      - target_mode: ID from config ('general', 'developer', 'analyst').
      - intent: The specific GOAL to be achieved in the NEW mode.
      - summary: A CONCISE RECAP of the interactions in the CURRENT mode.
          IMPORTANT RULES for Summary:
          1. TERMINOLOGY: Refer to the human as "Helper", NOT "User".
          2. CONTENT: Do NOT just say "Helper asked to switch". 
             Instead, summarize the actual work done or discussed (e.g., "Discussed RPG mechanics, Helper suggested a dragon character").
             This ensures the next mode understands what happened previously.
    SIDE EFFECT: Triggers system events and prompt reconfiguration.
    """,
    "flow.continue": """
SIGNATURE: flow.continue(next_step: str)
TYPE: [VISIBLE]
DESCRIPTION: Forces immediate continuation without waiting for user input.
PARAMS:
  - next_step: Short description of the next logical step.
""",

    # --- KNOWLEDGE ---
    "knowledge.memorize": """
SIGNATURE: knowledge.memorize(essence: str, lesson: str, emotions: List[str], weight: float)
TYPE: [SILENT]
DESCRIPTION: Saves knowledge to long-term vector memory.
PARAMS:
  - essence: Factual summary (1-2 sentences).
  - lesson: Actionable advice for future.
  - emotions: List of emotion tags.
  - weight: 0.0-1.0 importance (default 0.8).
""",
    "knowledge.add_tool_insight": """
SIGNATURE: knowledge.add_tool_insight(target_tool: str, insight: str)
TYPE: [SILENT]
DESCRIPTION: Saves a technical "best practice" or warning about a tool into the permanent tool-usage knowledge base (use.json).
USE THIS WHEN:
  - You failed to use a tool correctly and figured out why.
  - You discovered a clever way to use a tool.
  - You want to warn your future self about a parameter quirk.
PARAMS:
  - target_tool: The exact name of the tool (e.g., 'system.write_file').
  - insight: A concise, instructional sentence (e.g., 'Always verify the folder exists before writing.').
""",
    "knowledge.recall_context": """
SIGNATURE: knowledge.recall_context(query: str)
TYPE: [VISIBLE]
DESCRIPTION: Vector search for past memories.
PARAMS:
  - query: Search topic/concept.
""",
    "knowledge.recall_emotion": """
SIGNATURE: knowledge.recall_emotion(emotions: List[str])
TYPE: [VISIBLE]
DESCRIPTION: Search memories by emotional tags using EXACT filtering.
PARAMS:
  - emotions: List of emotion tags.
  IMPORTANT: Use the Standard English tags listed in the Global Instructions above.
""",
    "knowledge.ask": """
SIGNATURE: knowledge.ask(question: str, restart: bool)
TYPE: [VISIBLE]
DESCRIPTION: Ask external LLM/Internet for facts.
PARAMS:
  - question: Query text.
  - restart: If True, clears search history.
""",
    "knowledge.thinking": """
SIGNATURE: knowledge.thinking(context: str)
TYPE: [SILENT]
DESCRIPTION: Trigger deep internal thought (Monologue thread).
PARAMS:
  - context: The dilemma or topic to analyze.
""",
    "knowledge.propose_law": """
SIGNATURE: knowledge.propose_law(name: str, text: str)
TYPE: [SILENT]
DESCRIPTION: Propose new internal law for the Constitution.
""",

    # --- SYSTEM ---
    "system.read_file": """
SIGNATURE: system.read_file(store: str, path: str)
TYPE: [VISIBLE]
DESCRIPTION: Read file content.
PARAMS:
  - store: 'a','b','c','n','temp'.
  - path: Relative path.
""",
    "system.list_folder": """
SIGNATURE: system.list_folder(store: str, path: str)
TYPE: [VISIBLE]
DESCRIPTION: List directory contents.
PARAMS:
  - store: 'a','b','c','n','temp'.
  - path: Relative path (default ".").
""",
    "system.write_file": """
SIGNATURE: system.write_file(store: str, path: str, content: str)
TYPE: [VISIBLE]
DESCRIPTION: Write/Overwrite file.
PARAMS:
  - store: MUST be 'n' (incubator) or 'temp'. FORBIDDEN: 'b'.
  - path: Relative path.
  - content: Full text content.
""",
    "system.edit_file": """
SIGNATURE: system.edit_file(store: str, path: str, find: str, replace: str)
TYPE: [VISIBLE]
DESCRIPTION: Replace text block in file.
PARAMS:
  - store: 'n' or 'temp'.
  - path: Relative path.
  - find: Exact match string.
  - replace: New string.
""",
    "system.copy_file": """
SIGNATURE: system.copy_file(from_store: str, from_path: str, to_store: str, to_path: str)
TYPE: [VISIBLE]
DESCRIPTION: Copy file between stores.
PARAMS:
  - to_store: MUST be 'n' or 'temp'.
""",
    "system.dump": """
SIGNATURE: system.dump(target_store: str, filename: str)
TYPE: [VISIBLE]
DESCRIPTION: Dump whole store to single file in 'temp'.
PARAMS:
  - target_store: Store to dump.
  - filename: Output filename in 'temp'.
""",

    # --- GAME ---
    "game.llama": """
SIGNATURE: game.llama(message: str, restart: bool)
TYPE: [VISIBLE]
DESCRIPTION: Chat with Creative Persona.
""",
    "game.oss": """
SIGNATURE: game.oss(message: str, restart: bool)
TYPE: [VISIBLE]
DESCRIPTION: Chat with Logical Persona.
""",

    # --- INFO ---
    "info.tools": """
SIGNATURE: info.tools(target: str = "all")
TYPE: [VISIBLE]
DESCRIPTION: The universal manual for tool usage.
PARAMS:
  - target:
      * "all": Returns general rules + list of ALL tools.
      * "group_name" (e.g., "system", "flow"): Returns detailed manual for that category.
      * "tool_name" (e.g., "system.write_file"): Returns specific details for that single tool.
"""
}