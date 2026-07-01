# WIZOR backend — Python 3.12 (стек залочен PRD §12).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости для asyncpg/сборки — минимальны (psycopg не используем).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала метаданные — кешируем слой зависимостей.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip && pip install -e .

COPY alembic.ini ./
COPY migrations ./migrations

EXPOSE 8000

# Прод-запуск: миграции применяются отдельным шагом (CI/entrypoint), не в CMD.
CMD ["uvicorn", "wizor.main:app", "--host", "0.0.0.0", "--port", "8000"]
