<!-- HEAD-SUMMARY (≤500т): Стек WIZOR (PRD §12, заблокирован). Backend: Python 3.12/FastAPI/Pydantic v2/SQLAlchemy+Alembic. Данные: Postgres 16+pgvector/Redis 7/Celery. Auth: Keycloak. Frontend: Next.js 15/React 19/shadcn. Crawler: Crawlee+Playwright+httpx+tenacity. AI: провайдер-agnostic router, RU-default (GigaChat/YandexGPT), OSS fallback (vLLM). Инфра: Yandex Cloud (РФ) + Hetzner/Selectel (probe). Биллинг: ЮKassa. Аналитика: PostHog self-hosted. Не повторять версии в phase-файлах. -->

# Tech Stack — единый источник правды WIZOR

> PRD §12 baseline-constraint. Смена версии/провайдера = обновить здесь + ADR.

## Backend

| Слой | Версия / Библиотека | Фаза |
|---|---|---|
| Language | Python 3.12+ (match, strict type hints) | P1 |
| Framework | FastAPI + uvicorn | P1 |
| Validation | Pydantic v2 | P1 |
| ORM | SQLAlchemy 2.x + Alembic | P1 |
| Async I/O | httpx + asyncpg + redis.asyncio | P1 |
| Task queue | Celery + Redis | P2 |
| Logging | structlog JSON + OpenTelemetry | P1 |

## Данные

| Слой | Технология | Фаза | Заметки |
|---|---|---|---|
| Основная БД | PostgreSQL 16 | P1 | `tenant_id` с дня 1 |
| Vector | pgvector | P3 | Qdrant → фаза C (on-prem/нагрузки) |
| Кеш / очереди | Redis 7 | P1 | Celery + rate-limit + sessions |

## Auth

Keycloak self-hosted (OIDC, multi-tenancy, JWT) — P1.

## Frontend

| Слой | Версия | Фаза |
|---|---|---|
| Framework | Next.js 15 (React 19), TypeScript 5.x strict | P7 |
| Компоненты | shadcn/ui + Tailwind CSS | P7 |
| Графики | Recharts (продукт), Plotly (отчёты) | P7/P8 |
| State | React Hook Form + Zod, Zustand, TanStack Query | P7 |

## Crawler / Probe

| Слой | Технология | Фаза |
|---|---|---|
| Краулер | Crawlee (Python) / Scrapy + Playwright (SPA) | P2 |
| Прокси | Smartproxy / Bright Data (резидентные) | P5 |
| HTTP | httpx + tenacity (retry, ротация) | P2 |
| Schema-валидация | rdflib + custom JSON-LD validator | P2 |

## AI / ML

| Слой | Технология | Фаза | Заметки |
|---|---|---|---|
| LLM-router | Собственная provider-agnostic абстракция | P4 | NFR-3; минимум LangChain |
| RU-default | GigaChat (Сбер) + YandexGPT / Yandex Cloud FM | P4 | контент клиента только RU |
| Probe (зарубеж.) | OpenAI, Perplexity, Anthropic | P5 | через зарубежные ноды + прокси |
| Probe (RU) | Yandex Cloud Foundation Models (Алиса/Нейро) | P5 | с RU-IP |
| OSS fallback | vLLM + Qwen 2.5 / Saiga | P6 | batch-cost |
| Embeddings | YandexGPT Emb. / GigaChat Emb. + BGE-M3 | P3 | |
| MCP SDK | @modelcontextprotocol/sdk | Фаза C | Integration layer |

## Инфра / DevOps

| Слой | Технология | Фаза | Заметки |
|---|---|---|---|
| Cloud РФ | Yandex Cloud ru-central1 | P1 | 152-ФЗ; NFR-1 |
| Cloud probe | Hetzner / Selectel | P5 | ChatGPT/Perplexity не с РФ-IP |
| CI/CD | GitLab CI / GitHub Actions; Docker → K8s+Helm+ArgoCD | P1/B | |
| Observability | Grafana+Prometheus+Loki+Tempo+Sentry | P1 | |
| Secrets | Vault / Yandex Lockbox | P1 | |
| Аналитика | PostHog self-hosted | P1 | North Star NFR-7 |

## Биллинг

ЮKassa (РФ, карты + СБП, физ+юр) — P9. Stripe (экспорт) — фаза B.

## CMS-коннекторы

WordPress (P10 / нед. 7) → Tilda (A.4) → 1C-Битрикс (A.4) → Modx/OpenCart (B) → Magento/Shopify/headless (C).
