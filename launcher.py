"""Portable launcher: loopback-only WSGI server and a separately stoppable worker."""
import argparse
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir")
    args = parser.parse_args()
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_config.settings")
    if args.data_dir:
        os.environ["APA_DATA_DIR"] = str(Path(args.data_dir).resolve())
    elif getattr(sys, "frozen", False):
        os.environ.setdefault("APA_DATA_DIR", str(Path(sys.executable).parent / "data"))
    if args.worker:
        import django
        django.setup()
        from platform_app.jobs import worker
        worker()
        return
    url = f"http://127.0.0.1:{args.port}"
    try:
        with urllib.request.urlopen(url + "/health/", timeout=1) as response:
            if b'"version": "0.1.0"' in response.read():
                if not args.no_browser:
                    webbrowser.open(url)
                print(url, flush=True)
                return
    except Exception:
        pass
    import django
    django.setup()
    from django.core.management import call_command
    from platform_app.jobs import seed_profile
    call_command("migrate", interactive=False, verbosity=0)
    seed_profile()
    from django.conf import settings
    log_dir = settings.DATA_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    import logging
    logging.basicConfig(filename=log_dir / "application.log", level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    command = ([sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(root / "launcher.py")]) + ["--worker"]
    worker_log = (log_dir / "worker.log").open("a", encoding="utf-8")
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=worker_log, stderr=worker_log,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from platform_config.wsgi import application
    from waitress import create_server
    server = None
    try:
        server = create_server(StaticFilesHandler(application), host="127.0.0.1", port=args.port, threads=6,
                               max_request_body_size=32 * 1024 * 1024)
        print(f"APA Thesis Checker: {url}", flush=True)
        print("Stop: Ctrl+C / close this window. / Остановка: Ctrl+C / закройте окно.", flush=True)
        if not args.no_browser:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        if server:
            server.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        worker_log.close()


if __name__ == "__main__":
    main()
