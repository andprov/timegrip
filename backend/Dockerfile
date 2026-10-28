FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM python:3.13-slim AS runtime

RUN python -m pip uninstall -y pip

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app src ./src

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000

CMD ["python", "-m", "timegrip"]
