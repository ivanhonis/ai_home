import os
from pathlib import Path

# Root directory (starting point of traversal)
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent

# Folders to ignore
IGNORE_FOLDERS = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    ".idea",
    ".mypy_cache",
    "!Archive",
    "images",
    "!dump",
    "tokens",
    "!docs",
    "docs",
    "!proto",
}

# File extensions to include
INCLUDE_EXTENSIONS = {".py", ".html", ".yaml", ".md", ".css"}


def should_ignore_dir(dir_name: str) -> bool:
    return dir_name in IGNORE_FOLDERS


def collect_files(root: Path):
    collected = []
    for current_root, dirs, files in os.walk(root):
        # Filter directories in-place for os.walk
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]

        for fname in files:
            path = Path(current_root) / fname
            if path.suffix in INCLUDE_EXTENSIONS:
                collected.append(path)

    # Sort by full path
    collected.sort(key=lambda p: str(p))
    return collected


def dump_directory(root: Path, output_file: Path):
    files = collect_files(root)

    with output_file.open("w", encoding="utf-8", errors="ignore") as out:
        for path in files:
            rel_path = path.relative_to(root)

            # Header at the start of each file
            out.write("\n" + "=" * 80 + "\n")
            out.write(f"FILE: {rel_path}\n")
            out.write("=" * 80 + "\n\n")

            try:
                with path.open("r", encoding="utf-8") as f:
                    out.write(f.read())
            except UnicodeDecodeError:
                # If we can’t read it cleanly, try again with errors ignored
                with path.open("r", encoding="utf-8", errors="ignore") as f:
                    out.write(f.read())

            out.write("\n\n")  # small gap between files


def main():
    # 1) Full project dump (docs folder is skipped because of IGNORE_FOLDERS)
    project_output = OUTPUT_DIR / "project_dump.txt"
    dump_directory(ROOT_DIR, project_output)
    print(f"Done: {project_output}")

    # 2) Separate dump only for the docs folder
    docs_root = ROOT_DIR / "docs"
    docs_output = OUTPUT_DIR / "docs_dump.txt"

    if docs_root.exists() and docs_root.is_dir():
        dump_directory(docs_root, docs_output)
        print(f"Done: {docs_output}")
    else:
        print(f"Warning: 'docs' folder does not exist at path: {docs_root}")


if __name__ == "__main__":
    main()
