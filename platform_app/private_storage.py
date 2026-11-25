"""Server-only PDF storage. No public object URLs or client credentials."""
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from .checker import MAX_SIZE, PDFError


@contextmanager
def pdf_local_path(file):
    try:
        path = file.path
    except NotImplementedError:
        path = None
    if path is not None:
        yield path
        return
    with tempfile.TemporaryDirectory(prefix='apa-private-') as directory:
        path = Path(directory) / 'input.pdf'
        count = 0
        with file.open('rb') as source, path.open('wb') as target:
            for chunk in source.chunks(1024 * 1024):
                count += len(chunk)
                if count > MAX_SIZE:
                    raise PDFError('too_large')
                target.write(chunk)
        yield path


@deconstructible
class PrivateCloudStorage(Storage):
    def __init__(self, endpoint=None, token=None):
        self.endpoint = (endpoint or settings.APA_STORAGE_ENDPOINT).rstrip('/')
        self.token = token or settings.APA_STORAGE_TOKEN
        parsed = urlsplit(self.endpoint)
        if not self.token or (parsed.scheme != 'https' and parsed.hostname not in ('127.0.0.1', 'localhost')):
            raise ValueError('Private storage requires HTTPS and a server token')

    @staticmethod
    def safe_name(name):
        parts = name.split('/')
        if not name or any(p in ('', '.', '..') for p in parts) or '\\' in name or not name.endswith('.pdf'):
            raise ValueError('Invalid private PDF object name')
        return name

    def request(self, method, name, data=None):
        name = self.safe_name(name)
        request = Request(self.endpoint + '?name=' + quote(name, safe=''), data=data, method=method,
            headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/pdf'})
        try:
            return urlopen(request, timeout=90)
        except HTTPError as exc:
            status = exc.code
            exc.close()
            if status == 404:
                raise FileNotFoundError(name) from None
            raise OSError('Private PDF storage unavailable') from None
        except (URLError, TimeoutError):
            raise OSError('Private PDF storage unavailable') from None

    def _open(self, name, mode='rb'):
        if mode not in ('r', 'rb'):
            raise ValueError('Read-only handle')
        with self.request('GET', name) as response:
            data = response.read(MAX_SIZE + 1)
        if len(data) > MAX_SIZE:
            raise OSError('Private PDF exceeds file size limit')
        return ContentFile(data, name=name)

    def _save(self, name, content):
        data = content.read(MAX_SIZE + 1)
        if len(data) > MAX_SIZE or not data.startswith(b'%PDF-'):
            raise OSError('Invalid private PDF')
        with self.request('PUT', name, data) as response:
            response.read(1024)
        return name

    def exists(self, name):
        try:
            with self.request('HEAD', name):
                return True
        except FileNotFoundError:
            return False

    def delete(self, name):
        try:
            with self.request('DELETE', name) as response:
                response.read(1024)
        except FileNotFoundError:
            pass

