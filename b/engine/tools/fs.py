import logging
import sys
from typing import Dict, Any, List

# Configuration
from .config import BASE_DIR

# --- PROJECT FS GUARDIAN INTEGRATION ---
try:
    project_root = BASE_DIR.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # Import class
    from project_fs import ProjectFSGuardian
except ImportError:
    raise ImportError("CRITICAL ERROR: 'project_fs.py' not found in project root!")

# Initialize Guardian (Root is parent of 'b/')
guardian = ProjectFSGuardian(root=BASE_DIR.parent, n_folder_name="n", temp_folder_name="temp")
logger = logging.getLogger(__name__)


# --- SYSTEM TOOLS ---

def read_file(args: Dict[str, Any]) -> str:
    store = args.get("store")
    path = args.get("path")
    if not store or not path: return "Error: 'store' and 'path' are mandatory."
    try:
        return guardian.read_text(store, path)
    except Exception as e:
        return f"Error: {e}"


def list_folder(args: Dict[str, Any]) -> str:
    store = args.get("store")
    path = args.get("path", ".")
    if not store: return "Error: 'store' is mandatory."
    try:
        items = guardian.list_dir(store, path)
        lines = []
        for item in items:
            prefix = "<DIR>" if item["is_dir"] else "<FILE>"
            lines.append(f"{prefix} {item['relative_path']}")
        return "\n".join(sorted(lines)) if lines else "Empty directory."
    except Exception as e:
        return f"Error: {e}"


def write_file(args: Dict[str, Any]) -> str:
    store = args.get("store")
    path = args.get("path")
    content = args.get("content", "")
    if not store or not path: return "Error: missing parameters."
    try:
        res = guardian.write_text(store, path, content)
        return f"Write successful: {res}"
    except Exception as e:
        return f"Error: {e}"


def edit_file(args: Dict[str, Any]) -> str:
    store = args.get("store")
    path = args.get("path")
    find_text = args.get("find")
    replace_text = args.get("replace")
    if not store or not path or not find_text: return "Error: missing parameters."
    try:
        return guardian.replace_in_file(store, path, find_text, replace_text)
    except Exception as e:
        return f"Error: {e}"


def copy_file(args: Dict[str, Any]) -> str:
    from_store = args.get("from_store")
    from_path = args.get("from_path")
    to_store = args.get("to_store")
    to_path = args.get("to_path")
    if not all([from_store, from_path, to_store, to_path]): return "Error: missing parameters."
    try:
        return guardian.copy_file(from_store, from_path, to_store, to_path)
    except Exception as e:
        return f"Error: {e}"


def create_dump(args: Dict[str, Any]) -> str:
    target_store = args.get("target_store")
    filename = args.get("filename", f"dump_{target_store}.txt")

    if not target_store: return "Error: target_store is mandatory."

    try:
        # Manually verify valid store for listing
        if target_store not in ['a', 'b', 'c', 'n']:
            return "Error: Can only dump 'a', 'b', 'c', or 'n'."

        # 1. Recursive list (We use guardian list_dir but need to recurse manually if we want full dump)
        # Simplified: We rely on a helper to walk via guardian?
        # Since guardian.list_dir is shallow, we need a recursive implementation here utilizing guardian.

        all_files = []

        def _recurse(current_path):
            items = guardian.list_dir(target_store, current_path)
            for item in items:
                # relative_path coming from guardian is full project path (e.g. b/engine/test.py)
                # but we need sub-path relative to store for recursion logic?
                # Actually guardian.list_dir takes path relative to store root.

                # We need the name/path relative to the folder we are listing
                local_rel = item['name']
                if current_path != ".":
                    local_rel = f"{current_path}/{item['name']}"

                if item["is_dir"]:
                    _recurse(local_rel)
                else:
                    # Just store the path relative to store root for reading
                    all_files.append(local_rel)

        _recurse(".")

        # Filter (e.g., .py only or everything? User said full dump. Let's keep it generally text)
        all_files.sort()

        # 2. Concat
        content_lines = [f"# FULL DUMP OF STORE: {target_store}", f"# FILES: {len(all_files)}\n"]

        for fpath in all_files:
            content_lines.append(f"\n{'=' * 60}\nFILE: {fpath}\n{'=' * 60}\n")
            try:
                text = guardian.read_text(target_store, fpath)
                content_lines.append(text)
            except:
                content_lines.append("[BINARY OR ERROR]")

        full_content = "\n".join(content_lines)

        # 3. Write to TEMP
        res = guardian.write_text("temp", filename, full_content)
        return f"Dump created in TEMP: {res}"

    except Exception as e:
        return f"Dump error: {e}"