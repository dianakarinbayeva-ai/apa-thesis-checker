# Free cloud deployment implementation plan

> Use superpowers:executing-plans for inline execution.

**Goal:** Run the existing full Django application at an HTTPS URL using only free services.

**Architecture:** Render Free runs one web process and a supervised PDF worker. Supabase Free stores Django tables in an unexposed private schema and PDF objects in a private bucket. A narrow, authenticated Edge Function mediates object operations without exposing Supabase service credentials. SQLite and filesystem storage remain the Windows defaults.

**Authorization:** User requested deployment, safe tests, GitHub publication and explicitly accepted foreign hosting of the protected 37-student roster. Both account spaces were confirmed; quoted Supabase cost is $0/month. No paid resource or upgrade is permitted.

**Constraints:** Python 3.12, Django 5.2, no new system installs, no private data in source, preserve local data, no public first-user administrator, no static replacement. Free hosts can sleep and have quotas.

## Work

- [ ] Test remote file processing and storage CRUD, error handling, path rejection and cleanup; observe failures, implement bounded private storage and temporary processing.
- [ ] Test PostgreSQL URL parsing and fail-closed cloud settings; implement private schema, HTTPS, static serving and same-container worker lifecycle.
- [ ] Provision dedicated database role/schema and private bucket; deploy authenticated storage function; verify anonymous denial and private CRUD.
- [ ] Run migrations and synthetic HTTP account, ownership, upload, queue and report checks; review changes and publish sanitized source.
- [ ] Create Render Free service, verify real HTTPS URL and security boundaries; migrate local accounts, roster, history and files privately with counts and hashes.
- [ ] Verify restart persistence, source archive exclusions, provider security advisors and complete instructions with actual URL and free-tier limits.

## Review focus

Reject traversal and oversized remote objects; clean temporary PDFs after errors. Fail closed if cloud secrets are missing. Ensure private Django tables are absent from public REST. Keep the worker alive and stop it when web exits. Never overwrite or clear local student data during migration.
