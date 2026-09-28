[![RU](https://img.shields.io/badge/README-RU-red.svg)](README.ru.md)

# TimeGrip

[![License: AGPL-3.0](https://img.shields.io/github/license/andprov/timegrip?color=blueviolet)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**An open-source time tracker you can run on your own server.** Organize work
into projects, track hours with a live timer or manual entries, and see what
your time is worth: set an hourly rate per project and billable amounts are
calculated for you.

[**Try it at timegrip.ru**](https://timegrip.ru) ·
[API reference](https://timegrip.ru/api/docs) ·
[Android app](https://github.com/andprov/timegrip-client/releases)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/img/home/Dashboard-dark.png">
  <img alt="TimeGrip dashboard" src="frontend/public/img/home/Dashboard-light.png">
</picture>

## Features

- **Projects.** Color-code them, archive finished ones without losing their
  history, and set an hourly rate per project.
- **Live or manual tracking.** Start a timer when you begin working, or add
  and edit entries afterwards. Overlapping entries are caught automatically.
- **Billing.** Billable amounts are calculated from the project rate, with
  optional rounding to the nearest hour.
- **Reports.** Pick any date range, filter by project or billable status,
  group totals by project or by day, and export to CSV.
- **Any screen.** Responsive interface for desktop and mobile, light and dark
  themes, English and Russian.
- **REST API.** Everything the app does goes through a documented API, so you
  can build your own integrations.
- **Android app.** A [native client](https://github.com/andprov/timegrip-client)
  that works with the same account, in the cloud or on your own server.
- **Offline Android client.** Start a timer with no connection; all entries
  sync once you are back online.
- **The rate is stored with each entry.** Changing a project's rate does not
  recalculate past entries, so amounts you have already billed stay the same.

<table>
  <tr>
    <td><img alt="Projects" src="frontend/public/img/home/Projects-2-light.png"></td>
    <td><img alt="Timers" src="frontend/public/img/home/Timers-2-light.png"></td>
    <td><img alt="Reports" src="frontend/public/img/home/Reports-light.png"></td>
  </tr>
</table>

## Why TimeGrip

- **Your data stays with you.** Cloud services keep all your data on their
  side. TimeGrip can run on your own server.
- **Free, with no pricing plans.** All features are available for free.
- **Nothing extra.** Unlike most platforms that try to be complex enterprise
  suites, TimeGrip has only the features you need to track time and calculate
  what it is worth.
- **Open source.** Licensed under AGPL-3.0.

## Quick start

You need a Linux server (`amd64` or `arm64`, a Raspberry Pi works too) with
Docker, ports `80` and `443` open, and a domain pointing to it. The
repository is not needed, only three files from the latest release:

```bash
mkdir timegrip && cd timegrip
base=https://github.com/andprov/timegrip/releases/latest/download
curl -fLO $base/docker-compose.yml
curl -fL $base/env.example -o .env
curl -fL $base/seo.config.example.json -o seo.config.json
```

In `.env`, set `DOMAIN`, `SECRET_KEY` (a random string, for example the
output of `openssl rand -hex 32`), `POSTGRES_PASSWORD` and the `SMTP_*`
settings of your mail account. In `seo.config.json`, set `siteUrl` and
`title`, or run without SEO by adding `SEO_CONFIG_FILE=/dev/null` to `.env`.
Then start:

```bash
docker compose up -d
```

Open `https://<your domain>/`: the site works over HTTP right away and
switches to HTTPS once the Let's Encrypt certificate is issued, usually within
a minute or two. Updates, certificates and backups are covered in
[docs/DEPLOY.md](docs/DEPLOY.md).

## Try it locally

> [!NOTE]
> For a look around or development only: the images are built from source,
> the site runs over HTTP on `localhost` without certificates, and emails go
> to a log instead of being sent. To run TimeGrip for real, use
> [Quick start](#quick-start).

With Docker installed:

```bash
git clone https://github.com/andprov/timegrip.git
cd timegrip
cp .env.example .env
```

In `.env`, set `SECRET_KEY` to a random string (for example, the output of
`openssl rand -hex 32`) and `EMAIL_SENDER_BACKEND=console`. With the console
backend, emails such as sign-up activation codes are written to the
`outbox_email` service log instead of being sent. Then start the stack:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Open `http://localhost/`. The API reference is at `http://localhost/api/docs`.

To look around with sample data (10 projects, about three months of entries),
load [tools/seed/seed.sql](tools/seed/seed.sql) and sign in as
`user@example.com` / `Passw0rd`:

```bash
docker compose -f docker-compose.dev.yml exec -T db psql -U postgres -d timegrip < tools/seed/seed.sql
```

## Documentation

- [docs/DEPLOY.md](docs/DEPLOY.md): production deployment from the published
  images (amd64 and arm64, including Raspberry Pi) with HTTPS, configuration,
  and SEO
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): running the backend and frontend
  without Docker, tests, and linting

## Tech stack

```text
backend/    FastAPI + Postgres
frontend/   React + Vite SPA
gateway/    nginx reverse proxy and certbot (Let's Encrypt certificates)
```

## License

[AGPL-3.0](LICENSE)
