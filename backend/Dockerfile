FROM python:3.13-slim AS builder

WORKDIR /app

RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .


FROM python:3.13-slim AS runtime

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app src ./src

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000

CMD ["python", "-m", "timegrip"]
