# Free cloud deployment / Тегін хостинг / Бесплатный хостинг

**Live URL:** [apa-thesis-checker.onrender.com](https://apa-thesis-checker.onrender.com/). **Curator:** [/curator/](https://apa-thesis-checker.onrender.com/curator/), after signing in.

The full Python application runs on **Render Free**, with durable **Supabase Free** PostgreSQL and private PDF storage. The Windows ZIP continues to work independently with SQLite and local files.

Толық Python платформасы **Render Free** серверінде, деректері **Supabase Free** жабық базасы мен PDF қоймасында сақталады. Windows нұсқасы SQLite және жергілікті файлдармен бөлек жұмыс істейді.

Полная Python-платформа работает на **Render Free**, данные — в **Supabase Free** PostgreSQL и закрытом PDF-хранилище. Windows-версия независимо использует SQLite и локальные файлы.

## Limits / Шектеулер / Ограничения

- Render Free sleeps after 15 minutes without requests. Opening the site again can take about one minute. One web instance contains both the web server and supervised PDF worker. No paid worker, disk or database is used.
- Supabase Free provides 500 MB database, 1 GB storage and limited monthly traffic. Projects can pause after a week of inactivity. These plans are not a guarantee of permanent availability. Do not enable paid upgrades or artificial keep-alive requests.
- Render Free-де 15 минут әрекетсіздіктен кейін сайт ұйқы режиміне өтеді; қайта ашылуы бір минуттай уақыт алуы мүмкін. Supabase Free базасы 500 МБ, файл қоймасы 1 ГБ; бір апта әрекетсіздіктен кейін жоба тоқтатылуы мүмкін.
- Render Free засыпает после 15 минут без запросов; пробуждение может занять около минуты. Supabase Free: база 500 МБ, файлы 1 ГБ; после недели бездействия проект могут приостановить.
- Source: [Render](https://render.com/docs/free), [Supabase pricing](https://supabase.com/pricing). Checked 2026-11-25. No payment method or upgrade is required by this configuration.

## Server configuration

Use Python 3.12.14, build `pip install -r requirements.txt`, start `python cloud_launcher.py`, plan **free**, one instance. Render sets `PORT` and `RENDER_EXTERNAL_HOSTNAME`. Set server-only environment variables using the provider's Environment page or authenticated management tools:

The current service was connected through its public repository URL. For this connection method, a GitHub push alone does not redeploy it: select **Manual Deploy → Deploy latest commit** in the Render dashboard after publishing reviewed changes. Alternatively, connect the GitHub provider to enable automatic deployments. See [Render deployment documentation](https://render.com/docs/deploys).

| Variable | Value |
| --- | --- |
| APA_CLOUD | `1` |
| APA_HTTPS | `1` |
| APA_DATA_DIR | `/tmp/apa-runtime` (temporary runtime data only) |
| DATABASE_URL | Supabase session pooler PostgreSQL URL, dedicated `apa_app` role |
| DJANGO_SECRET_KEY | Stable random secret; retain the existing local secret when migrating enrollment codes |
| APA_STORAGE_ENDPOINT | HTTPS URL of the deployed private-storage gateway |
| APA_STORAGE_TOKEN | Random server token, at least 40 characters; never sent to the browser |

Do not set wildcard hosts. `/health/` is a lightweight status endpoint. Render's reverse proxy is trusted for HTTPS and client-IP forwarding; `cloud_launcher.py` must only bind behind that proxy. The Windows launcher continues binding only to loopback.

Create the `apa_private` schema owned by a dedicated login role with no administrative privileges. The Django role needs ownership for migrations. Keep the schema outside exposed API schemas; revoke access from `PUBLIC`, `anon`, `authenticated`. Enable RLS without public policies on app tables. Ownership allows only the backend role to access these tables; Django enforces student ownership and curator group scopes.

Deploy `scripts/storage-gateway.ts` as `apa-private-storage` with its `__APA_TOKEN_SHA256__` placeholder replaced by the SHA256 of the random server token. The function authenticates requests itself before any storage access, so deploy it with JWT verification disabled. Supabase service credentials remain inside the function's standard environment. Call authenticated `POST ?operation=initialize` once to create/configure the private `apa-private-pdfs` bucket with a 30 MB PDF limit. No anonymous object policies or public bucket URLs are allowed. All file operations must pass Django authorization first.

The web server and worker share PostgreSQL and private storage. Temporary copies used by PyMuPDF are bounded and deleted after checking. Ephemeral Render files are never the durable store. A dead web server or worker causes the service to exit so the host can restart it. Interrupted processing is explicitly failed after its stale-job timeout rather than falsely marked successful.

## Private migration and backups

Back up SQLite consistently before migration. Transfer users with password hashes, groups, rule profiles, roster and submissions privately; exclude browser sessions. Upload original PDFs to the private bucket retaining their database names. Check row counts and SHA256 hashes before opening access. Do not import private exports into Git, source ZIPs or release assets. Local and cloud installations are separate databases after migration; changes do not synchronize automatically.

Деректер көшірілгеннен кейін жергілікті және интернеттегі нұсқалар бөлек болады. Өзгерістер автоматты түрде синхрондалмайды. Жеке резервтік көшірмелерді GitHub-қа салмаңыз.

После переноса локальная и облачная версии используют отдельные базы. Изменения автоматически не синхронизируются. Частные резервные копии нельзя публиковать на GitHub.

## Safe verification

Use synthetic accounts/documents for registration, login, student/curator isolation, upload → worker → report, PDF/JSON downloads, three languages and restart persistence. Remove synthetic records and objects afterwards. Check HTTPS, CSRF, secure cookies, private bucket denial, private-schema REST denial and source archive exclusions. Run Supabase security advisors after migrations. Load real rosters only after these checks pass.
