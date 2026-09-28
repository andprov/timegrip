# Deploy TimeGrip

Running the whole stack with Docker Compose, locally or on a server with
HTTPS. For local development without Docker, see
[DEVELOPMENT.md](DEVELOPMENT.md).

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
interface in [frontend/plugins/seo.ts](../frontend/plugins/seo.ts).

The values are baked into `index.html`, `robots.txt` and `sitemap.xml` at
build time. Without the file `npm run build` emits no SEO tags. A config at
another path can be passed with the `SEO_CONFIG` environment variable.

In Docker the file stays out of the build context and image layers:
[docker-compose.yml](../docker-compose.yml) passes it to the frontend build as a
secret, and the build fails if the file is missing. Set `SEO_CONFIG_FILE` in
`.env` to use another path, or `SEO_CONFIG_FILE=/dev/null` to build without
SEO tags. [docker-compose.dev.yml](../docker-compose.dev.yml) does not pass the
config.

Docker's build cache does not track secrets, so after changing the config
rebuild the frontend without it:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Run all in Docker

Both Compose files start the same services with the same nginx config from
[gateway/nginx/](../gateway/nginx/):

- [docker-compose.yml](../docker-compose.yml) — production: HTTPS for `DOMAIN`
  and the `certbot` service, see
  [Deploy to production](#deploy-to-production-https)
- [docker-compose.dev.yml](../docker-compose.dev.yml) — local run: HTTP on
  `localhost`, Postgres published on `127.0.0.1:5433`

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Starts Postgres, runs Alembic migrations (`migrate`, one-off), then the
API (`api`), `frontend`, and `outbox_email` worker as long-running
services, and `nginx` in front of them all.

The `cleanup` worker is one-shot, so its container loops it with a
`sleep` in between runs (see the `cleanup` service command in
[docker-compose.yml](../docker-compose.yml), interval hardcoded to 3600s).

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

In `.env` (section `DEPLOY` of [.env.example](../.env.example)):

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
webroot) are in [gateway/certbot/cli.ini](../gateway/certbot/cli.ini).

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
