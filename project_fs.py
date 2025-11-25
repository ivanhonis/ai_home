# project_fs.py
from pathlib import Path
from typing import Optional
import shutil


class ProjectFSGuardian:
    """
    - root alatt BÁRMIT olvashat (read_text, list_dir, stb.)
    - írni CSAK az n/ mappán belül tud (write_text_in_n)
    """

    def __init__(self, root: Path, n_folder_name: str = "n") -> None:
        self.root = root.resolve()
        self.n_root = (self.root / n_folder_name).resolve()

    # ----------- belső biztonsági segédfüggvények -----------

    def _ensure_under_root(self, path: Path) -> Path:
        real = path.resolve()
        # ha nem a root alatt van, relative_to hibát dob
        real.relative_to(self.root)
        return real

    def _ensure_under_n(self, path: Path) -> Path:
        real = path.resolve()
        # ha nem az n/ alatt van, relative_to hibát dob
        real.relative_to(self.n_root)
        return real

    # ------------------ OLVASÁS: bármi root alatt ------------------

    def read_text(self, relative_path: str, max_bytes: int = 200_000_000) -> str:
        """
        relative_path: a gyökérhez viszonyított elérési út (pl. 'engine/tools.py', 'b/memory.json')
        max_bytes: ennyit olvas maximum (LLM miatt érdemes limitálni)
        """
        target = self._ensure_under_root(self.root / relative_path)
        data = target.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="replace")

    def list_dir(self, relative_dir: str = ".") -> list[dict]:
        """
        Visszaadja egy könyvtár tartalmát metaadatokkal.
        Csak olvas: nem módosít semmit.
        """
        dir_path = self._ensure_under_root(self.root / relative_dir)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Nem könyvtár: {dir_path}")

        entries = []
        for p in dir_path.iterdir():
            entries.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "relative_path": str(p.relative_to(self.root))
            })
        return entries

    # ------------------ ÍRÁS: CSAK n/ alatt ------------------

    def write_text_in_n(self, relative_path: str, content: str, mode: str = "w") -> str:
        """
        Csak az n/ mappán belül írhat.
        relative_path: útvonal az n/ gyökeréhez képest (pl. 'drafts/idea1.txt')
        mode: 'w' vagy 'a'
        Visszaadja a tényleges fájl abszolút elérési útját stringként.
        """
        target = self._ensure_under_n(self.n_root / relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open(mode, encoding="utf-8") as f:
            f.write(content)
        return str(target)

    # --- ÚJ METÓDUS 1 ---
    def copy_to_n(self, source_relative_path: str, dest_relative_path_in_n: str) -> str:
        """
        Átmásol egy fájlt a projekt gyökeréből (pl. 'b/main.py')
        a biztonságos n/ mappán belüli helyre.
        """
        try:
            # 1. Forrás validálása (root alatt bárhol lehet)
            source_path = self._ensure_under_root(self.root / source_relative_path)
            if not source_path.is_file():
                raise FileNotFoundError(f"A forrásfájl nem található: {source_relative_path}")

            # 2. Cél validálása (CSAK n/ alatt lehet)
            dest_path = self._ensure_under_n(self.n_root / dest_relative_path_in_n)

            # 3. Másolás
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, dest_path)

            return f"Sikeres másolás: {source_relative_path} -> {dest_path.relative_to(self.root)}"
        except Exception as e:
            return f"Hiba a másolás közben: {e}"

    # --- ÚJ METÓDUS 2 ---
    def find_and_replace_in_n(self, relative_path_in_n: str, find_text: str, replace_text: str) -> str:
        """
        Keres és cserél egy szövegrészletet egy FÁJLBAN,
        amely KIZÁRÓLAG az n/ mappán belül található.
        """
        try:
            # 1. Célfájl validálása (CSAK n/ alatt lehet)
            target_path = self._ensure_under_n(self.n_root / relative_path_in_n)
            if not target_path.is_file():
                raise FileNotFoundError(f"A célfájl nem található az n/ mappán belül: {relative_path_in_n}")

            # 2. Olvasás
            content = target_path.read_text("utf-8")

            # 3. Csere
            if find_text not in content:
                return f"A keresett szöveg ('{find_text}') nem található. Nem történt módosítás."

            modified_content = content.replace(find_text, replace_text)

            # 4. Visszaírás
            target_path.write_text(modified_content, "utf-8")

            return f"Sikeres csere a fájlban: {target_path.relative_to(self.root)}"
        except Exception as e:
            return f"Hiba a csere közben: {e}"
