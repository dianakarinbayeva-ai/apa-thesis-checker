"""Build on Windows. Source archive is an explicit allowlist, never the data dir."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parent
os.chdir(root)
sys.path.insert(0, str(root))
from platform_app.source_bundle import source_archive

build = root / "build"
build.mkdir(exist_ok=True)
(build / "source.zip").write_bytes(source_archive())
args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--name", "APA Thesis Checker",
        "--collect-all", "django", "--collect-all", "pymupdf", "--collect-all", "reportlab",
        "--hidden-import", "platform_config.settings", "--hidden-import", "platform_config.urls",
        "--hidden-import", "platform_config.wsgi", "--hidden-import", "platform_app.views",
        "--hidden-import", "platform_app.models", "--hidden-import", "platform_app.admin",
        "--hidden-import", "platform_app.management.commands.worker", "--collect-submodules", "platform_app.migrations",
        "--add-data", "platform_app/templates;platform_app/templates",
        "--add-data", "platform_app/static;platform_app/static",
        "--add-data", "platform_app/assets;platform_app/assets",
        "--add-data", "build/source.zip;.", "launcher.py"]
subprocess.run(args, check=True)
folder = root / "dist" / "APA Thesis Checker"
for name in ("LICENSE", "NOTICE.md", "README.ru.md", "README.kk.md", "README.en.md", "start.cmd"):
    shutil.copy2(root / name, folder / name)
import importlib.metadata
notices = folder / "third-party-licenses"
notices.mkdir(exist_ok=True)
for distribution in importlib.metadata.distributions():
    for entry in distribution.files or []:
        if any(word in entry.name.lower() for word in ("license", "copying", "notice")) and '.dist-info' in str(entry):
            source = distribution.locate_file(entry)
            if source.is_file():
                target = notices / distribution.metadata['Name'] / entry.name
                target.parent.mkdir(exist_ok=True)
                shutil.copy2(source, target)
python_licence = Path(sys.base_prefix) / 'LICENSE.txt'
if python_licence.is_file():
    shutil.copy2(python_licence, notices / 'Python-LICENSE.txt')
archive = root.parent / "apa-thesis-checker-v0.1.0-windows-x64.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
    for file in folder.rglob("*"):
        if file.is_file():
            zipped.write(file, str(Path("APA Thesis Checker") / file.relative_to(folder)))
print(archive)
