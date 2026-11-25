"""Single free web instance: WSGI plus a supervised, separate PDF worker."""
import logging
import os
from pathlib import Path
import signal
import subprocess
import sys
from threading import Event, Thread


def main():
    os.environ.setdefault('APA_CLOUD', '1')
    os.environ.setdefault('APA_DATA_DIR', '/tmp/apa-runtime')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'platform_config.settings')
    from platform_config.cloud import validate_cloud_environment
    validate_cloud_environment(os.environ)
    import django
    django.setup()
    from django.core.management import call_command
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from platform_app.jobs import seed_profile
    from platform_config.wsgi import application
    from waitress import create_server
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')
    call_command('migrate', interactive=False, verbosity=0)
    seed_profile()
    # Only bind behind the hosting provider's reverse proxy. The local launcher is loopback-only.
    server = create_server(StaticFilesHandler(application), host='0.0.0.0',
        port=int(os.environ.get('PORT', '8000')), threads=4,
        trusted_proxy='*', trusted_proxy_count=1,
        trusted_proxy_headers={'x-forwarded-proto','x-forwarded-for'},
        max_request_body_size=32*1024*1024)
    process = None
    thread = Thread(target=server.run, daemon=True)
    stopping = Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopping.set())
    try:
        process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('manage.py')), 'worker'],
            stdin=subprocess.DEVNULL)
        thread.start()
        print('APA cloud web server and PDF worker ready', flush=True)
        while not stopping.wait(0.5):
            if process.poll() is not None or not thread.is_alive():
                raise RuntimeError('A cloud service process stopped; restart required')
    finally:
        server.close()
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        thread.join(timeout=5)


if __name__ == '__main__':
    main()
