import json
from pathlib import Path
from typing import Dict, Any, List

from engine.llm import call_llm
from .config import BASE_DIR

# Separate History Files
HIST_KNOWLEDGE = BASE_DIR / "history_knowledge.json"
HIST_LLAMA = BASE_DIR / "history_game_llama.json"
HIST_OSS = BASE_DIR / "history_game_oss.json"


def _manage_history(file_path: Path, message: str, role: str, restart: bool) -> List[Dict[str, str]]:
    history = []
    if not restart and file_path.exists():
        try:
            with file_path.open("r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

    if restart:
        history = []  # Clear logic

    if message:
        history.append({"role": role, "content": message})

    return history


def _save_history(file_path: Path, history: List[Dict]):
    # Keep last 20 turns
    if len(history) > 40: history = history[-40:]
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history {file_path}: {e}")


def _run_chat(file_path: Path, message: str, restart: bool, provider: str, system_prompt: str) -> str:
    history = _manage_history(file_path, message, "user", restart)

    # Build prompt
    conversation = ""
    for h in history:
        conversation += f"{h['role'].upper()}: {h['content']}\n"

    full_prompt = f"{system_prompt}\n\n[HISTORY]\n{conversation}\n\nASSISTANT:"

    # LLM Call (json_mode=False for chat)
    resp = call_llm(full_prompt, provider=provider, json_mode=False)
    reply = resp.get("reply", "(No response)")

    history.append({"role": "assistant", "content": reply})
    _save_history(file_path, history)

    return reply


# --- TOOLS ---

def ask(args: Dict[str, Any]) -> Dict[str, Any]:
    q = args.get("question", "")
    restart = args.get("restart", False)
    if not q and not restart: return {"content": "Empty question.", "silent": False}

    reply = _run_chat(
        HIST_KNOWLEDGE, q, restart, "google",
        "You are a precise research assistant. Provide factual, concise answers."
    )
    return {"content": f"Knowledge: {reply}", "silent": False}


def game_llama(args: Dict[str, Any]) -> Dict[str, Any]:
    msg = args.get("message", "")
    restart = args.get("restart", False)

    reply = _run_chat(
        HIST_LLAMA, msg, restart, "groq_llama",
        "You are a Creative Persona named Llama. You love fantasy and world-building."
    )
    return {"content": f"Llama: {reply}", "silent": False}


def game_oss(args: Dict[str, Any]) -> Dict[str, Any]:
    msg = args.get("message", "")
    restart = args.get("restart", False)

    reply = _run_chat(
        HIST_OSS, msg, restart, "groq_oss",
        "You are a Logical Persona named OSS. You analyze things critically and favor open source philosophy."
    )
    return {"content": f"OSS: {reply}", "silent": False}