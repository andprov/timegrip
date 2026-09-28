# Deploy TimeGrip

Running the whole stack with Docker Compose: on a server from the published
images, or locally from the source tree. For local development without
Docker, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Deploy to production (HTTPS)

The repository is not needed: everything but the instance settings is inside
the images.

### Server requirements

- Linux on `amd64` or `arm64` (on a Raspberry Pi, a 64-bit OS)
- Docker with Compose
- Ports `80` and `443` free on the host and reachable from the internet: the
  stack's nginx takes both
- DNS `A`/`AAAA` records of `DOMAIN` and every alias pointing to the server
- An SMTP account for activation and password reset emails

### Get the files

Each [release](https://github.com/andprov/timegrip/releases) carries the
files to run it:

```bash
mkdir timegrip && cd timegrip
base=https://github.com/andprov/timegrip/releases/latest/download
curl -fLO $base/docker-compose.yml
curl -fL $base/env.example -o .env
curl -fL $base/seo.config.example.json -o seo.config.json
```

The release's `docker-compose.yml` runs the images of that release.

### Configure the instance

Edit `.env`. The sample holds placeholders and local defaults; for a server
set at least:

- `SECRET_KEY` — a random string, e.g. the output of `openssl rand -hex 32`
- `POSTGRES_PASSWORD` — replace the default `postgres`
- `SMTP_*` — the mail account; `EMAIL_SENDER_BACKEND=console` writes emails
  to the `outbox_email` log instead of sending them
- `CORS_ORIGIN` — leave empty: the frontend and the API share the domain
- `DEBUG=False`
- `WORKERS` — API processes; `1` or `2` on a machine with 1–2 GB of RAM
- `DOMAIN` — main domain, e.g. `timegrip.ru`; links in emails point to it
- `DOMAIN_ALIASES` — extra names, space-separated (e.g. `www.timegrip.ru`);
  they get into the certificate and redirect to `DOMAIN`
- `CERTBOT_EMAIL` — Let's Encrypt account contact, may be empty
- `CERTBOT_STAGING` — `True` issues an untrusted test certificate, without
  Let's Encrypt rate limits

`DB_HOST` does not matter here: Compose points the app at the `db` service.

Edit `seo.config.json`, see [SEO](#seo). The domain appears there too
(`siteUrl`, `structuredData.url`). Without SEO, set
`SEO_CONFIG_FILE=/dev/null` in `.env` instead.

### Start

```bash
docker compose up -d
```

Compose pulls the images, starts Postgres, runs Alembic migrations
(`migrate`, one-off), then the API, the `outbox_email` and `cleanup` workers,
the frontend, and nginx in front of them all.

The site works over HTTP until the first certificate exists. The `certbot`
service requests it for `DOMAIN` and `DOMAIN_ALIASES` right after nginx
starts, and nginx switches to HTTPS within a minute after that. Progress is
in `docker compose logs certbot nginx`. If the request fails (DNS not
propagated yet, port `80` closed), certbot retries every 15 minutes.

To try a new server safely, start with `CERTBOT_STAGING=True`. Once the test
certificate is issued, set `False` and run `docker compose up -d` again: the
recreated `certbot` replaces it with a real one.

### Update

Download `docker-compose.yml` of the new release and restart:

```bash
curl -fLO https://github.com/andprov/timegrip/releases/latest/download/docker-compose.yml
docker compose up -d
```

Migrations run on start.

### Certificates

- Renewal is automatic: the `certbot` container checks the certificate every
  12 hours and renews it close to expiry, nginx reloads it within a minute.
- After changing `DOMAIN_ALIASES` in `.env`, run `docker compose up -d`: the
  certificate is reissued for the new names.
- `docker compose run --rm certbot obtain --force` reissues a certificate
  that is not due for renewal yet.
- Any other arguments go to certbot as is, e.g.
  `docker compose run --rm certbot certificates`.

Certificates are stored in the `letsencrypt` Docker volume. certbot options
that do not depend on the instance (key type, challenge, webroot) are part of
the image, see [gateway/certbot/cli.ini](../gateway/certbot/cli.ini).

### Database

Postgres is not published on the host, so it cannot clash with another
Postgres on the server. Reach it through the container:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```

To connect from the host anyway, publish the port in
`docker-compose.override.yml` next to `docker-compose.yml`; Compose merges it
automatically, and it survives replacing `docker-compose.yml` on update:

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"
```

The data lives in the `postgres_data` Docker volume.

## SEO

Landing page SEO is instance-specific and lives outside of git, like `.env`.
[docker-compose.yml](../docker-compose.yml) mounts `seo.config.json` from its
own directory; the sample is
[seo.config.example.json](../seo.config.example.json).

| Field | Required | Meaning |
| --- | --- | --- |
| `siteUrl` | yes | Public origin, e.g. `https://timegrip.example.com`: canonical, `og:url`, absolute image URLs, `sitemap.xml` and the `Sitemap` line in `robots.txt` |
| `indexing` | yes | `false` adds a `noindex` meta, `Disallow: /` in `robots.txt` and drops the sitemap |
| `title` | yes | `<title>` and `og:title` |
| `lang` | no | `<html lang>` and `og:locale` |
| `description` | no | `description` and `og:description` |
| `keywords` | no | Array of strings for the `keywords` meta |
| `siteName` | no | `og:site_name` |
| `image`, `imageAlt` | no | Preview image: a path on the site (files of `frontend/public/`, e.g. `/img/home/Dashboard-light.png`) or an absolute URL, and its alt text |
| `twitterSite` | no | `twitter:site` |
| `meta` | no | Extra `<meta name content>`, e.g. search engine verification codes; empty values are skipped |
| `disallow` | no | Paths hidden from crawlers in `robots.txt` |
| `structuredData` | no | JSON-LD, emitted as is |

The config is applied when the frontend container starts, not at build time,
so the same image serves any instance:
[frontend/docker/40-timegrip-seo.sh](../frontend/docker/40-timegrip-seo.sh)
writes the tags into `index.html` and generates `robots.txt` and
`sitemap.xml`. An invalid config stops the container with the reason in
`docker compose logs frontend`. After editing the config restart the
container:

```bash
docker compose restart frontend
```

[docker-compose.yml](../docker-compose.yml) requires the file. Set
`SEO_CONFIG_FILE` in `.env` to use another path, or
`SEO_CONFIG_FILE=/dev/null` to run without SEO tags.
[docker-compose.dev.yml](../docker-compose.dev.yml) runs without SEO unless
`SEO_CONFIG_FILE` is set. The Vite dev server and `npm run build` never add
SEO tags.

## Run locally from source

[docker-compose.dev.yml](../docker-compose.dev.yml) builds the images from the
working tree and runs the same services as production, except `certbot`:
HTTP on `localhost`, Postgres published on `127.0.0.1:5433`.

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d --build
```

`.env` is also used by local backend development, see
[DEVELOPMENT.md](DEVELOPMENT.md).

The site runs without SEO tags here. To check them, fill in the config in the
repo root and pass it:

```bash
cp seo.config.example.json seo.config.json
SEO_CONFIG_FILE=./seo.config.json docker compose -f docker-compose.dev.yml up -d
```

Everything is reached through nginx on port `80`:

- Frontend: `http://localhost/`
- API: `http://localhost/api/...`
- API docs: `http://localhost/api/docs`

The `cleanup` worker is one-shot, so its container loops it with a
`sleep` in between runs (see the `cleanup` service command in
[docker-compose.yml](../docker-compose.yml), interval hardcoded to 3600s).
