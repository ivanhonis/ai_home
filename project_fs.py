# project_fs.py
from pathlib import Path
from typing import Optional
import shutil


class ProjectFSGuardian:
    """
    - Can read ANYTHING under root (read_text, list_dir, etc.)
    - Can write ONLY inside the n/ and temp/ folders.
    """

    def __init__(self, root: Path, n_folder_name: str = "n", temp_folder_name: str = "temp") -> None:
        self.root = root.resolve()
        self.n_root = (self.root / n_folder_name).resolve()
        self.temp_root = (self.root / temp_folder_name).resolve()

    # ----------- Internal Security Helpers -----------

    def _ensure_under_root(self, path: Path) -> Path:
        real = path.resolve()
        # raises relative_to error if not under root
        real.relative_to(self.root)
        return real

    def _ensure_writable(self, path: Path) -> Path:
        """
        Ensures the path is inside a writable directory (n/ or temp/).
        """
        real = path.resolve()

        # Check if it is under n/ OR temp/
        is_in_n = False
        is_in_temp = False

        try:
            real.relative_to(self.n_root)
            is_in_n = True
        except ValueError:
            pass

        try:
            real.relative_to(self.temp_root)
            is_in_temp = True
        except ValueError:
            pass

        if not (is_in_n or is_in_temp):
            raise ValueError(f"Write permission denied. Path must be under 'n/' or 'temp/'. Path: {path}")

        return real

    def _resolve_store_path(self, store: str, relative_path: str) -> Path:
        """
        Helper to construct path from store identifier.
        store: 'a', 'b', 'c', 'n', 'temp'
        """
        if store not in ['a', 'b', 'c', 'n', 'temp']:
            raise ValueError(f"Invalid store: {store}")

        base = self.root / store
        # Handle cases where relative_path starts with ./ or /
        clean_rel = relative_path.lstrip("./\\")
        full_path = base / clean_rel
        return self._ensure_under_root(full_path)

    # ------------------ READING: Anything under root ------------------

    def read_text(self, store: str, relative_path: str, max_bytes: int = 200_000_000) -> str:
        target = self._resolve_store_path(store, relative_path)
        if not target.exists():
            return "File not found."

        if not target.is_file():
            return "Path is a directory, not a file."

        data = target.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="replace")

    def list_dir(self, store: str, relative_dir: str = ".") -> list[dict]:
        dir_path = self._resolve_store_path(store, relative_dir)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")

        entries = []
        for p in dir_path.iterdir():
            entries.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "relative_path": str(p.relative_to(self.root))  # Return full project relative path
            })
        return entries

    # ------------------ WRITING: ONLY under n/ or temp/ ------------------

    def write_text(self, store: str, relative_path: str, content: str) -> str:
        """
        Writes (overwrites) file. Store MUST be 'n' or 'temp'.
        """
        if store not in ['n', 'temp']:
            raise ValueError("Write allowed only in 'n' or 'temp' stores.")

        target = self._resolve_store_path(store, relative_path)
        self._ensure_writable(target)  # Double check

        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            f.write(content)
        return str(target.relative_to(self.root))

    def copy_file(self, from_store: str, from_path: str, to_store: str, to_path: str) -> str:
        """
        Copies file. Destination store MUST be 'n' or 'temp'.
        """
        source = self._resolve_store_path(from_store, from_path)
        if not source.is_file():
            raise FileNotFoundError(f"Source file not found: {from_store}/{from_path}")

        if to_store not in ['n', 'temp']:
            raise ValueError("Destination allowed only in 'n' or 'temp' stores.")

        dest = self._resolve_store_path(to_store, to_path)
        self._ensure_writable(dest)

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, dest)
        return f"Copy successful: {source.name} -> {to_store}/{to_path}"

    def replace_in_file(self, store: str, relative_path: str, find_text: str, replace_text: str) -> str:
        """
        Text replacement. Store MUST be 'n' or 'temp'.
        """
        if store not in ['n', 'temp']:
            raise ValueError("Edit allowed only in 'n' or 'temp' stores.")

        target = self._resolve_store_path(store, relative_path)
        self._ensure_writable(target)

        if not target.is_file():
            raise FileNotFoundError(f"File not found: {store}/{relative_path}")

        content = target.read_text("utf-8")
        if find_text not in content:
            return f"The search text ('{find_text}') was not found. No changes made."

        modified_content = content.replace(find_text, replace_text)
        target.write_text(modified_content, "utf-8")
        return f"Replacement successful in: {store}/{relative_path}"