import logging
import sys
from typing import Dict, Any, List

# Configuration
from .config import BASE_DIR

# --- PROJECT FS GUARDIAN INTEGRATION ---
# Attempt to import the central FS guardian from the root.
try:
    # Add project root to path if not present
    project_root = BASE_DIR.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from project_fs import ProjectFSGuardian
except ImportError:
    # Fallback or error if not found
    raise ImportError("CRITICAL ERROR: 'project_fs.py' not found in project root!")

# Initialize Guardian (Root is parent of 'b/')
guardian = ProjectFSGuardian(root=BASE_DIR.parent, n_folder_name="n")
logger = logging.getLogger(__name__)


# --- HELPER FUNCTIONS ---

def _resolve_store_path(store: str, path: str) -> str:
    """
    Joins store and path into a relative path understood by Guardian.
    (e.g., store='b', path='main.py' -> 'b/main.py')
    """
    # If path is '.', list only the store directory
    if path == "." or path == "./":
        return store

    # Remove leading ./
    clean_path = path.lstrip("./")
    return f"{store}/{clean_path}"


def _recursive_collect_files(relative_dir: str, collected_files: List[str]):
    """
    Recursively collects files using Guardian's list_dir method.
    Required for project.dump tool.
    """
    try:
        items = guardian.list_dir(relative_dir)
        for item in items:
            if item["is_dir"]:
                _recursive_collect_files(item["relative_path"], collected_files)
            else:
                collected_files.append(item["relative_path"])
    except Exception as e:
        logger.warning(f"Error during recursive traversal ({relative_dir}): {e}")


# --- FILE SYSTEM TOOLS (DELEGATION TO GUARDIAN) ---

def read_project(args: Dict[str, Any]) -> str:
    store = args.get("store")
    path = args.get("path")
    if not store or path is None:
        return "fs.read: Error, store and path are mandatory."

    full_rel_path = _resolve_store_path(store, path)
    try:
        # Delegation to Guardian
        content = guardian.read_text(full_rel_path)
        return content if content else "Empty file."
    except Exception as e:
        return f"Error: {e}"


def list_project(args: Dict[str, Any]) -> str:
    store = args.get("store")
    path = args.get("path", ".")
    if not store:
        return "fs.list: Error, store is mandatory."

    full_rel_path = _resolve_store_path(store, path)
    try:
        # Delegation to Guardian
        items = guardian.list_dir(full_rel_path)
        lines = []
        for item in items:
            prefix = "<DIR>" if item["is_dir"] else "<FILE>"
            # Display only name or relative path? Tool spec says path.
            lines.append(f"{prefix} {item['relative_path']}")

        return "\n".join(sorted(lines)) if lines else "Empty directory."
    except Exception as e:
        return f"Error: {e}"


def write_n(args: Dict[str, Any]) -> str:
    # Path is relative to 'n' folder!
    rel_path_in_n = args.get("path")
    content = args.get("content", "")
    mode = args.get("mode", "w")

    if not rel_path_in_n:
        return "fs.write_n: missing path."

    try:
        # Delegation to Guardian
        abs_path = guardian.write_text_in_n(rel_path_in_n, content, mode)
        return f"Write successful: {abs_path}"
    except Exception as e:
        return f"Error: {e}"


def copy_to_n(args: Dict[str, Any]) -> str:
    source_path = args.get("source_path")  # Relative to ROOT
    dest_path_in_n = args.get("dest_path_in_n")  # Relative to 'n'

    if not source_path or not dest_path_in_n:
        return "fs.copy_to_n: missing parameters."

    try:
        # Delegation to Guardian
        result = guardian.copy_to_n(source_path, dest_path_in_n)
        return result
    except Exception as e:
        return f"Error: {e}"


def replace_in_n(args: Dict[str, Any]) -> str:
    path_in_n = args.get("path_in_n")
    find_text = args.get("find_text")
    replace_text = args.get("replace_text")

    if not path_in_n or not find_text or replace_text is None:
        return "fs.replace_in_n: missing parameter."

    try:
        # Delegation to Guardian
        result = guardian.find_and_replace_in_n(path_in_n, find_text, replace_text)
        return result
    except Exception as e:
        return f"Error: {e}"


def project_dump(args: Dict[str, Any]) -> str:
    """
    Saves the entire storage.
    Since Guardian has no 'dump' method, we manually traverse the directory
    using Guardian's 'list_dir' and 'read_text' methods to adhere to rules.
    """
    store_name = args.get("store")
    output_filename = args.get("output_path_in_n", f"project_dump_{store_name}.txt")

    if not store_name:
        return "project.dump: store is mandatory."

    try:
        # 1. Collect files recursively (via Guardian)
        all_files = []
        # Store name itself is root relative path (e.g. 'b')
        _recursive_collect_files(store_name, all_files)

        # Only .py files (legacy logic, can be expanded)
        py_files = [f for f in all_files if f.endswith(".py")]
        py_files.sort()

        # 2. Concatenate content
        dump_content = []
        dump_content.append(f"# PROJECT DUMP (STORE: {store_name})")
        dump_content.append(f"# TOTAL {len(py_files)} .py FILES\n")

        count = 0
        for file_rel_path in py_files:
            dump_content.append("\n" + "=" * 80)
            dump_content.append(f"FILE: {file_rel_path}")
            dump_content.append("=" * 80 + "\n")

            try:
                # Read content via Guardian
                file_content = guardian.read_text(file_rel_path)
                dump_content.append(file_content)
            except Exception as e:
                dump_content.append(f"[READ ERROR: {e}]")

            dump_content.append("\n")
            count += 1

        full_text = "\n".join(dump_content)

        # 3. Write to 'n' folder via Guardian
        guardian.write_text_in_n(output_filename, full_text)

        return f"project.dump: Save successful. {count} files saved to: n/{output_filename}"

    except Exception as e:
        return f"project.dump error: {e}"