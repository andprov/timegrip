[![EN](https://img.shields.io/badge/README-EN-red.svg)](README.md)

# TimeGrip

[![License: AGPL-3.0](https://img.shields.io/github/license/andprov/timegrip?color=blueviolet)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Трекер времени с открытым кодом, который можно развернуть на своём сервере.**
Ведите работу по проектам, учитывайте часы таймером или ручными записями и получайте данные о том, сколько стоит время потраченное на проект: задайте почасовую ставку для проекта, и сумма к оплате посчитается сама.

[**Попробовать на timegrip.ru**](https://timegrip.ru) ·
[Документация API](https://timegrip.ru/api/docs) ·
[Приложение для Android](https://github.com/andprov/timegrip-client/releases)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/public/img/home/Dashboard-dark.png">
  <img alt="Панель управления TimeGrip" src="frontend/public/img/home/Dashboard-light.png">
</picture>

## Возможности

- **Проекты.** Отмечайте их цветом, архивируйте завершённые без потери
  истории, задавайте почасовую ставку для каждого проекта.
- **Таймер или ручной учёт.** Запускайте таймер в начале работы или
  добавляйте и правьте записи потом. Пересечения записей отслеживаются
  автоматически.
- **Расчёт стоимости.** Сумма к оплате считается по ставке проекта, при
  желании с округлением до ближайшего часа.
- **Отчёты.** Любой период, фильтры по проекту и признаку оплаты, итоги по
  проектам или по дням, экспорт в CSV.
- **На любом экране.** Адаптивный интерфейс для компьютера и телефона,
  светлая и тёмная темы, русский и английский языки.
- **REST API.** Всё, что умеет приложение, доступно через задокументированный
  API, так что можно делать свои интеграции.
- **Приложение для Android.** [Нативный клиент](https://github.com/andprov/timegrip-client)
  работает с тем же аккаунтом, в облаке или на вашем сервере.

<table>
  <tr>
    <td><img alt="Проекты" src="frontend/public/img/home/Projects-2-light.png"></td>
    <td><img alt="Таймеры" src="frontend/public/img/home/Timers-2-light.png"></td>
    <td><img alt="Отчёты" src="frontend/public/img/home/Reports-light.png"></td>
  </tr>
</table>

## Почему TimeGrip

- **Данные остаются у вас.** Toggl Track и Clockify — облачные сервисы. TimeGrip можно развернуть на вашем сервере.
- **Бесплатно и без платных тарифов.** Все функции доступны.
- **Открытый код.** Лицензия AGPL-3.0.

## Быстрый старт

Нужен Docker:

```bash
git clone https://github.com/andprov/timegrip.git
cd timegrip
cp .env.example .env
```

В `.env` задайте `SECRET_KEY` случайной строкой (например, результатом
`openssl rand -hex 32`) и `EMAIL_SENDER_BACKEND=console`. Тогда письма,
например коды активации при регистрации, не отправляются, а пишутся в лог
сервиса `outbox_email`. Затем запустите:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Откройте `http://localhost/`. Документация API находится по адресу
`http://localhost/api/docs`.

Чтобы посмотреть приложение с данными (10 проектов, записи примерно за три
месяца), загрузите [tools/seed/seed.sql](tools/seed/seed.sql) и войдите как
`user@example.com` / `Passw0rd`:

```bash
docker compose -f docker-compose.dev.yml exec -T db psql -U postgres -d timegrip < tools/seed/seed.sql
```

## Документация

Документация на английском:

- [docs/DEPLOY.md](docs/DEPLOY.md): настройка, SEO и развёртывание в
  продакшене с HTTPS
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): запуск бэкенда и фронтенда без Docker, тесты и линтеры

## Стек

```text
backend/    FastAPI + Postgres
frontend/   React + Vite SPA
gateway/    nginx reverse proxy и certbot (сертификаты Let's Encrypt)
```

## Лицензия

[AGPL-3.0](LICENSE)
