import json
from typing import Dict, Any, List

# Central LLM caller of the system
from engine.llm import call_llm
from .config import BASE_DIR

# Context file will be in 'b/' directory
HISTORY_FILE = BASE_DIR / "external_chat_history.json"
MAX_HISTORY_ITEMS = 200


def _load_history() -> List[Dict[str, str]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def _save_history(history: List[Dict[str, str]]):
    if len(history) > MAX_HISTORY_ITEMS:
        history = history[-MAX_HISTORY_ITEMS:]
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR (remote.py): Failed to save chat history: {e}")


def network_chat(args: Dict[str, Any]) -> Dict[str, Any]:
    message = args.get("message", "")
    restart = args.get("restart", False)
    provider = args.get("provider", "groq")

    # History
    history = []
    if not restart:
        history = _load_history()

    if not message and not restart:
        return {"content": "ERROR: Empty message.", "silent": False}

    if message:
        history.append({"role": "user", "content": message})

    # Prompt construction
    conversation_text = ""
    for entry in history:
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        conversation_text += f"{role.upper()}: {content}\n"

    system_instruction = (
        "You are an external AI assistant connected via a chat interface. "
        "Maintain the conversation flow based on the history below. "
        "Be helpful, direct, and concise."
    )

    full_prompt = f"{system_instruction}\n\n[CHAT HISTORY]\n{conversation_text}\n\nASSISTANT:"

    # LLM Call - KEY POINT: json_mode=False
    try:
        response_data = call_llm(full_prompt, provider=provider, json_mode=False)

        reply_text = response_data.get("reply", "")
    except Exception as e:
        return {"content": f"Network error during external chat: {e}", "silent": False}

    if not reply_text:
        reply_text = "(No response from external network)"

    history.append({"role": "assistant", "content": reply_text})
    _save_history(history)
    return {
        "content": f"Groq: {reply_text}",
        "silent": False
    }