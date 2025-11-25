# ================================================================================
# FILE: b/engine/identity.py
# ================================================================================

from typing import Dict, Any, List
from .files import load_json, save_json

IDENTITY_FILE = "identity.json"

def load_identity() -> Dict[str, Any]:
    return load_json(IDENTITY_FILE, {
        "version": "1.0",
        "laws": [],
        "meta": {}
    })

def save_identity(identity: Dict[str, Any]):
    save_json(IDENTITY_FILE, identity)

def get_laws(identity: Dict[str, Any]) -> List[Dict[str, Any]]:
    return identity.get("laws", [])

def summarize_laws(identity: Dict[str, Any], max_chars: int = 1000) -> str:
    """
    Law of Context-Self: concise but present core of laws.
    Simple v1: merge into a short text and cut at max_chars.
    Can be smarter later.
    """
    pieces = []
    for law in identity.get("laws", []):
        name = law.get("name", "")
        text = law.get("text", "")
        pieces.append(f"{name}: {text}")
    full = "\n\n".join(pieces)
    return full[:max_chars]