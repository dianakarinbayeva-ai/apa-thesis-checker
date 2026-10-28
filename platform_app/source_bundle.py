import io
import sys
import zipfile
from pathlib import Path

TOP_FILES = {"manage.py", "launcher.py", "requirements.txt", "requirements-build.txt", "LICENSE", "NOTICE.md",
             "README.md", "README.ru.md", "README.kk.md", "README.en.md", ".gitignore", "Dockerfile", "compose.yml",
             "Caddyfile", ".dockerignore", "build_windows.py", "start.cmd"}
TOP_DIRS = {"platform_app", "platform_config", "vendor", "docs", "tests", ".github", "scripts"}


def distributable_files(root):
    root = Path(root)
    for file in root.rglob("*"):
        relative = file.relative_to(root)
        if not file.is_file() or any(p in {"__pycache__", ".git", "data", "build", "dist", ".venv"} for p in relative.parts):
            continue
        if file.suffix in {".pyc", ".log", ".sqlite3", ".zip"} or file.name == ".env":
            continue
        if (len(relative.parts) == 1 and file.name in TOP_FILES) or relative.parts[0] in TOP_DIRS:
            yield file, relative


def source_archive():
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "source.zip"
    if getattr(sys, "frozen", False) and bundled.is_file():
        return bundled.read_bytes()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for file, relative in distributable_files(Path(__file__).resolve().parent.parent):
            archive.write(file, str(relative))
    return out.getvalue()
