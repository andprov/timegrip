# Development

For developers: running the backend, workers and frontend
locally without Docker, loading test data into the database, and building and
linting the frontend. To just run the whole stack, see
[Run locally from source](DEPLOY.md#run-locally-from-source) in DEPLOY.md.

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

[tools/seed/seed.sql](../tools/seed/seed.sql) creates one active user with 10
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

## CI

[.github/workflows/ci.yml](../.github/workflows/ci.yml) runs on every push to
any branch: `ruff check`, `black --check` and `pytest` for the backend,
`npm run lint` and `npm run build` for the frontend.
