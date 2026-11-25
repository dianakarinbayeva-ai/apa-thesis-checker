"""Cloud database configuration; local Windows defaults remain in settings."""
from urllib.parse import unquote, urlsplit


def validate_cloud_environment(environment):
    required = ('DATABASE_URL','DJANGO_SECRET_KEY','APA_STORAGE_ENDPOINT','APA_STORAGE_TOKEN')
    if any(not environment.get(key) for key in required) or environment.get('APA_HTTPS') != '1':
        raise ValueError('Cloud deployment requires durable database, private storage, a stable secret and HTTPS')
    database_from_url(environment['DATABASE_URL'])
    if urlsplit(environment['APA_STORAGE_ENDPOINT']).scheme != 'https':
        raise ValueError('Cloud storage requires HTTPS')
    if len(environment['DJANGO_SECRET_KEY']) < 40 or len(environment['APA_STORAGE_TOKEN']) < 40:
        raise ValueError('Cloud secrets must have at least 40 characters')
    hosts = environment.get('ALLOWED_HOSTS') or environment.get('RENDER_EXTERNAL_HOSTNAME')
    if not hosts or '*' in hosts:
        raise ValueError('Explicit cloud hostnames are required')


def database_from_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('postgres', 'postgresql') or not parsed.hostname or not parsed.username or not parsed.password:
        raise ValueError('A complete PostgreSQL URL is required')
    return {'ENGINE':'django.db.backends.postgresql', 'NAME':unquote(parsed.path.lstrip('/')),
        'USER':unquote(parsed.username), 'PASSWORD':unquote(parsed.password),
        'HOST':parsed.hostname, 'PORT':str(parsed.port or 5432), 'CONN_MAX_AGE':60,
        'CONN_HEALTH_CHECKS':True,
        'OPTIONS':{'sslmode':'require', 'connect_timeout':15, 'options':'-c search_path=apa_private'}}
