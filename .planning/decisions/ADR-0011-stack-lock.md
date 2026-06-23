---
id: ADR-0011
title: stack-lock
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Стек зафиксирован по PRD §12 («boring tech»): Python/FastAPI, Next.js 15, Postgres+pgvector, Celery, Keycloak, Yandex Cloud; отклонение — только через ADR. -->

## Context

Окно рынка 12–18 месяцев (PRD §2.4). Экспериментирование со стеком на старте = замедление + нестабильность. Стек из PRD §12 выбран обоснованно (соответствует кадровым профилям PRD §9.6, РФ-compliance, проверен в production) и ИИ-агенты знают его «наизусть» (что снижает token-расход на документацию).

## Decision

Стек **заблокирован** согласно PRD §12 — «boring tech» без изменений:
- **Backend:** Python 3.12+, FastAPI + Pydantic v2, SQLAlchemy 2.x + Alembic.
- **Данные:** PostgreSQL 16 + pgvector (Qdrant — фаза C / нагрузки); Redis 7 (кеш / rate-limit / sessions); Celery + Redis/RabbitMQ (очереди).
- **Auth:** Keycloak (self-hosted, OIDC, multi-tenancy).
- **Frontend:** Next.js 15 (React 19), TypeScript 5.x, shadcn/ui + Tailwind, Recharts/Plotly, React Hook Form + Zod, Zustand / TanStack Query.
- **Crawler/probe:** Crawlee/Scrapy, Playwright, httpx + tenacity, rdflib + JSON-LD validator.
- **AI/ML:** LangChain/LlamaIndex минимально; embeddings RU (Yandex/GigaChat) + OSS (e5/BGE-M3); OSS LLM (vLLM + Qwen 2.5 / Saiga); MCP SDK (фаза C).
- **Инфра:** Yandex Cloud (РФ, 152-ФЗ) + Hetzner/Selectel (probe-нода); Docker → K8s (фаза C); GitLab CI / GitHub Actions; Grafana+Prometheus+Loki+Tempo; Sentry; Vault / Yandex Lockbox.
- **Биллинг/compliance:** ЮKassa; PostHog (self-host); Mailgun/Unisender.

Любое отклонение от стека — только через новый принятый ADR.

## Consequences

- Агенты не тратят токены на «выбор фреймворка»; всё известно заранее.
- Однозначный ответ на «какую технологию использовать» в любой задаче.
- Yandex Cloud как primary = 152-ФЗ-compliant хранение ПД клиентов по умолчанию.
- Компромисс: стек может устареть; пересмотр — только через ADR + аргументацию миграции.
- Qdrant и K8s отложены до фазы C — не усложняем MVP.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Django вместо FastAPI | Зрелость, admin | Медленнее для async; меньше подходит для API-first | FastAPI стандарт для новых Python API-сервисов |
| Qdrant с P1 | Лучший vector-search | Operational overhead; pgvector достаточен на MVP-нагрузках | Апгрейд по необходимости |
| AWS/GCP вместо Yandex Cloud | Больше сервисов | 152-ФЗ: ПД клиентов должны в РФ | Нарушает NFR-1 |

## Links

- Charter: `BUILD-CHARTER.md §2 (#15), §9`
- PRD: `PRD.md §12, §9.3 (NFR-1,NFR-2,NFR-3,NFR-6)`
- Related ADRs: ADR-0014 (dual-geo probe)
