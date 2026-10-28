# Linux / Kazakhstan deployment kit

No cloud account, paid service, domain or trial is ordered by this project.
The Windows package works without Docker. These instructions target a future
Kazakhstan Linux VPS (Ubuntu 24.04, 2 vCPU, 4 GB RAM recommended for a small pilot).

1. Install Docker Engine and Compose on the chosen server. Point a domain to it.
2. Copy the repository. Create `.env` locally on the server, not in Git:

```dotenv
DOMAIN=review.example.kz
POSTGRES_PASSWORD=GENERATE_A_LONG_RANDOM_PASSWORD
DJANGO_SECRET_KEY=GENERATE_A_DIFFERENT_LONG_RANDOM_SECRET
```

Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
in the server's private terminal. Never paste them into chat or commit them.

```sh
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

The init service runs migrations and collects static files. Caddy handles HTTPS.
Only ports 80/443 are published; database, worker and app stay internal.
First-user administrator promotion is disabled for cloud deployments.
One persistent worker claims jobs atomically; files remain outside public static
storage. Ten-minute abandoned jobs are failed explicitly rather than silently
marked complete. Application source remains downloadable at `/source/`.

## Backups and operations

Use a private administrator terminal; backup filenames must remain outside Git.

```sh
docker compose stop web worker
docker compose exec -T db pg_dump -U apa apa > database-backup.sql
docker compose run --rm --no-deps --user root -v "$PWD/backups:/backups" web tar czf /backups/application.tar.gz -C /data .
docker compose start web worker
```

Create `backups/` first, restrict permissions and store copies separately from the
server. Restore database and application volume together, then run migrations.
Use `docker compose logs --tail 100 web worker` and `/health/` for diagnosis.
The health endpoint establishes web liveness, not successful PDF processing;
verify a synthetic submission after upgrades. Do not log uploaded text or passwords.

Accounts use username/password. Email verification and emailed password recovery
are not included in the free pilot. Administrator password recovery:
`docker compose exec web python manage.py changepassword USERNAME`.
Review retention and self-registration policy with the Academy before broad use.

Initial release is a pilot. Start with a small group, measure processing latency
and memory, and expand only after checking real non-confidential samples.
Docker runtime verification requires Docker; it is not required on the user's Windows PC.
