# TimeGrip

TimeGrip is a service for tracking time spent on projects.
Register an account, organize your work into projects, and start or stop timers to measure exactly how much time goes into each one.

```bash
backend/    FastAPI + Postgres
frontend/   React + Vite SPA
gateway/    nginx reverse proxy and certbot (Let's Encrypt certificates)
```

## Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`. Required both by Docker (`docker-compose.yml` reads
it via `env_file: .env`) and by local backend development below.

## SEO

Landing page SEO is instance-specific and lives outside of git, like `.env`:

```bash
cp frontend/seo.config.example.json frontend/seo.config.json
```

Edit `frontend/seo.config.json`: `siteUrl`, title, description, preview image,
search engine verification codes (`meta`), paths hidden in `robots.txt`
(`disallow`) and JSON-LD (`structuredData`). Set `"indexing": false` to keep
the instance out of search engines. The field reference is the `SeoConfig`
interface in [frontend/plugins/seo.ts](frontend/plugins/seo.ts).

The values are baked into `index.html`, `robots.txt` and `sitemap.xml` at
build time. Without the file `npm run build` emits no SEO tags. A config at
another path can be passed with the `SEO_CONFIG` environment variable.

In Docker the file stays out of the build context and image layers:
[docker-compose.yml](docker-compose.yml) passes it to the frontend build as a
secret, and the build fails if the file is missing. Set `SEO_CONFIG_FILE` in
`.env` to use another path, or `SEO_CONFIG_FILE=/dev/null` to build without
SEO tags. [docker-compose.dev.yml](docker-compose.dev.yml) does not pass the
config.

Docker's build cache does not track secrets, so after changing the config
rebuild the frontend without it:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Run all in Docker

Both Compose files start the same services with the same nginx config from
[gateway/nginx/](gateway/nginx/):

- [docker-compose.yml](docker-compose.yml) — production: HTTPS for `DOMAIN`
  and the `certbot` service, see
  [Deploy to production](#deploy-to-production-https)
- [docker-compose.dev.yml](docker-compose.dev.yml) — local run: HTTP on
  `localhost`, Postgres published on `127.0.0.1:5433`

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Starts Postgres, runs Alembic migrations (`migrate`, one-off), then the
API (`api`), `frontend`, and `outbox_email` worker as long-running
services, and `nginx` in front of them all.

The `cleanup` worker is one-shot, so its container loops it with a
`sleep` in between runs (see the `cleanup` service command in
[docker-compose.yml](docker-compose.yml), interval hardcoded to 3600s).

Everything is reached through nginx on port `80`:

- Frontend: `http://localhost/`
- API: `http://localhost/api/...`
- API docs: `http://localhost/api/docs`

nginx picks its mode at start: with a certificate for `DOMAIN` it serves
HTTPS and redirects HTTP to it, without one it serves the site over HTTP.
Locally there is never a certificate.

## Deploy to production (HTTPS)

The server needs Docker, ports `80` and `443` open, and DNS `A`/`AAAA`
records of `DOMAIN` and every alias pointing to it.

### Configure the instance

In `.env` (section `DEPLOY` of [.env.example](.env.example)):

- `DOMAIN` — main domain, e.g. `timegrip.ru`; links in emails point to it
- `DOMAIN_ALIASES` — extra names, space-separated (e.g. `www.timegrip.ru`);
  they get into the certificate and redirect to `DOMAIN`
- `CERTBOT_EMAIL` — Let's Encrypt account contact, may be empty
- `CERTBOT_STAGING` — `True` issues an untrusted test certificate, without
  Let's Encrypt rate limits
- `CORS_ORIGIN` — leave empty: the frontend and the API share the domain
- `DEBUG=False`

The domain also appears in `frontend/seo.config.json` (`siteUrl`,
`structuredData.url`), see [SEO](#seo).

certbot options that do not depend on the instance (key type, challenge,
webroot) are in [gateway/certbot/cli.ini](gateway/certbot/cli.ini).

### First start

```bash
docker compose up -d --build
docker compose run --rm certbot obtain
docker compose restart nginx
```

Until a certificate exists the site works over HTTP. `obtain` issues the
certificate for `DOMAIN` and `DOMAIN_ALIASES`, and the restart switches nginx
to HTTPS.

To try a new server safely, run `obtain` with `CERTBOT_STAGING=True` first,
then set `False` and run `obtain` again — the test certificate is replaced
with a real one.

### Certificates

- Renewal is automatic: the `certbot` container runs `certbot renew` every
  12 hours, and nginx reloads the certificate every 6 hours.
- After changing `DOMAIN_ALIASES` or the key type in `cli.ini`, run
  `docker compose run --rm certbot obtain` and restart nginx.
- `docker compose run --rm certbot obtain --force` reissues a certificate
  that is not due for renewal yet.
- Any other arguments go to certbot as is, e.g.
  `docker compose run --rm certbot certificates`.

Certificates are stored in the `letsencrypt` Docker volume.

---

# DEV

This section is for developers: running the backend, workers and frontend
locally without Docker, loading test data into the database, and building and
linting the frontend. To just run the whole stack, see
[Run all in Docker](#run-all-in-docker) above.

## Run DEV backend

Local development without Docker — commands below assume `backend/` as the
working directory (`cd backend`). FastAPI + Postgres.

### Install backend dependencies

```bash
uv sync
```

`uv sync` installs everything into `backend/.venv`. The commands below run
through `uv run`, which uses that environment; alternatively activate it with
`source .venv/bin/activate` and drop the `uv run` prefix.

### Export environment variables

```bash
set -a; source ../.env; set +a
```

### Run migrations

```bash
alembic upgrade head
```

### Run the app

```bash
python -m timegrip
```

### Run workers

#### Outbox email worker

```bash
python -m timegrip.workers.outbox_email
```

#### Cleanup worker

```bash
python -m timegrip.workers.cleanup
```

### Run tests

```bash
pytest
```

### Lint and format

```bash
ruff check .
black --extend-exclude migrations .
```

Alembic migrations are generated code: `ruff` skips them via
`pyproject.toml`, and `--extend-exclude migrations` keeps `black` off them too.

## Load DB test data

[tools/seed/seed.sql](tools/seed/seed.sql) creates one active user with 10
projects and about three months of time entries counting back from today.
Re-running it replaces the previous seed data. Sign in with
`user@example.com` / `Passw0rd`.

Commands below assume the repo root as the working directory.

Load it (local dev, Postgres reachable on localhost:5432 per .env):

```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d timegrip -f tools/seed/seed.sql
```

Load it against a Docker Compose deployment (no host DB port needed):

```bash
docker compose -f docker-compose.dev.yml exec -T db psql -U postgres -d timegrip < tools/seed/seed.sql
```

## Run DEV frontend

Local development without Docker — commands below assume the repo root as
the working directory.

### Install frontend dependencies

```bash
npm --prefix frontend install
```

### Dev server

```bash
npm --prefix frontend run dev
```

Runs on `http://localhost:3000` (matches `CORS_ORIGIN` in `.env.example`) and
proxies `/api` to `http://localhost:8000` — run the backend separately (see
[Run DEV backend](#run-dev-backend) above).

If the backend runs elsewhere, point the proxy at it with
`VITE_API_PROXY_TARGET`. This is a real shell environment variable, not a
value from `.env` — `vite.config.ts` reads `process.env` directly:

```bash
VITE_API_PROXY_TARGET=http://localhost:9000 npm --prefix frontend run dev
```

### Build

```bash
npm --prefix frontend run build
```

Type-checks with `tsc -b` and outputs static files to `frontend/dist/`.

### Lint

```bash
npm --prefix frontend run lint
```
