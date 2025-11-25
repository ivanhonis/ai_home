import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent

def load_json(name: str, default: Any) -> Any:
    """Loads a JSON file relative to the base directory."""
    path = BASE_DIR / name
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(name: str, data: Any) -> None:
    """Saves data to a JSON file relative to the base directory."""
    path = BASE_DIR / name
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)