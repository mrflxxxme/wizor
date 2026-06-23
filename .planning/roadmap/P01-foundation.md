---
phase: P1
slug: foundation
title: "Foundation — репозиторий, CI, multi-tenant, observability, базовый стек"
status: planned
tier: 4
track: infra
depends_on: []
gated_by: []
contracts: [iam]
specialists: [devops-infra-specialist, compliance-152fz-specialist]
prd_refs: [§9.3/NFR-1, §9.3/NFR-7, FR-6.2, §12]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Инфра-фаза уровня 4. Создаёт monorepo, CI/CD, базовый стек FastAPI+Postgres(pgvector)+Redis+Celery, multi-tenant схему с tenant_id, PostHog self-hosted, Keycloak skeleton. Ни одна продуктовая фича не реализуется, но зато любая последующая фаза P2–P10 опирается на эту базу. 5-линзовый аудит (tier 4). -->

## Goal

Поднять полностью рабочий dev+CI-стэк, на который могут ложиться все последующие фазы. По итогу: монорепо с зелёным CI, `docker compose up` за ≤ 10 минут, multi-tenant-ready схема данных, PostHog трекинг активирован, Keycloak запущен.

## In scope

- Монорепо: `backend/`, `frontend/`, `infra/`, `scripts/`, `.github/workflows/`.
- **CI-пайплайны** (GitLab CI / GitHub Actions): backend (ruff + mypy + pytest + bandit + pip-audit), frontend (eslint + tsc + vitest + npm audit), security (gitleaks + trivy).
- **Docker Compose dev-стэк:** Postgres 16 + pgvector, Redis 7, Celery worker, Keycloak, backend (FastAPI), frontend (Next.js 15), Caddy reverse-proxy.
- **Multi-tenant модель данных:** `tenant_id UUID` на всех таблицах; RLS-политики или app-level фильтрация; схема изолирует тенантов, agency-миграция (P9) не потребует архитектурного рефакторинга (FR-6.2 AC).
- **Keycloak skeleton:** realm `wizor-dev`, client `wizor-api`, OIDC-flow настроен (только skeleton, полная auth → P9).
- **PostHog self-hosted** (NFR-7): `posthog:` сервис в compose, `POSTHOG_KEY` в `.env.example`; North Star события (`audit_started`, `fix_applied`, `score_calculated`) инструментируются как stubs.
- **Секреты:** `.env.example` с `TBD_*`-заглушками; Vault / Yandex Lockbox — stubs (реальное provisioning → prod-деплой).
- **Базовый FastAPI app:** `/health`, `/metrics` (Prometheus), `CORS`, structured JSON-логирование (Loki-ready).
- **Celery + Redis:** базовый worker, `ping`-таска для smoke-теста.
- **pgvector:** extension активирован в init-скрипте; `CREATE EXTENSION vector;` в миграции.
- **NFR-1 (152-ФЗ):** выбор хостинга зафиксирован (Yandex Cloud ru-central-1); в `.env.example` — только RU-регион.

## Out of scope

- Продуктовые эндпоинты (краулер, probe, score — → P2–P5).
- Keycloak полная auth с JWT-middleware (→ P9).
- Prod-деплой, Kubernetes, ArgoCD (→ devops в рамках P9/финальных фаз).
- Billing (→ P9).
- PostHog real events (→ P7+ при запуске Tier 0).

## Functional requirements

- **FR-P1-1** (из NFR-7): PostHog self-hosted развёрнут; SDK инициализирован в backend и frontend; stub-события (`page_viewed`, `audit_started`) отправляются и видны в PostHog UI.
- **FR-P1-2** (из FR-6.2): таблицы `tenants`, `sites`, `users` — все с `tenant_id`; схема изолирует тенантов; seed-скрипт создаёт тестового тенанта.
- **FR-P1-3** (из NFR-1): конфигурационный файл/README фиксирует, что ПД хранятся в Yandex Cloud ru-central-1; секреты вне кода.
- **FR-P1-4** (из §12): `Celery + Redis` worker запускается и отвечает на `ping`; очередь `default` работает.
- **FR-P1-5** (из §12): `pgvector` extension активен, тест `SELECT '[1,2,3]'::vector` проходит.

## Acceptance criteria

- **AC-1:** `git clone && cp .env.example .env && make dev-bootstrap` → exit 0, время ≤ 600 сек.
- **AC-2:** `make test` (pytest ≥70% coverage + vitest ≥70%) зелёный на fresh clone.
- **AC-3:** CI pipeline (3 workflow) зелёный; каждый ≤ 8 мин.
- **AC-4:** `GET /health` возвращает `{"status":"ok","tenant":"<id>"}` при наличии `X-Tenant-Id` заголовка.
- **AC-5:** PostHog UI показывает входящее тестовое событие из backend.
- **AC-6:** `SELECT tenant_id FROM sites WHERE tenant_id != '<test_tenant>'` → 0 строк (изоляция).
- **AC-7:** `celery inspect ping` → ответ от ≥1 worker.
- **AC-8:** `SELECT vector_dims('[1,2,3]'::vector)` → `3` (pgvector работает).

## Contracts touched

- `iam` — стаб: таблицы `tenants`, `users`; Keycloak realm skeleton; `tenant_id` как первичный ключ изоляции. API/events — JIT при P9.

## Exit-gate

| Критерий | Порог |
|---|---|
| `make dev-bootstrap` | exit 0, ≤ 600 сек |
| CI (3 workflow) | зелёный, каждый ≤ 8 мин |
| Test coverage | ≥70% |
| Multi-tenant изоляция | AC-6 пройден |
| PostHog self-hosted | тестовое событие видно в UI |
| Celery ping | ≥1 worker отвечает |
| pgvector | SELECT проходит |
| Аудит tier 4 | PASS (5 линз: correctness · security · compliance · tests · architecture) |

## Decomposition hints for planner

1. `devops-infra-specialist` создаёт `infra/docker-compose.dev.yml` со всеми сервисами + healthchecks.
2. `backend-implementer` поднимает FastAPI скелет (`/health`, `/metrics`, structured logging, CORS).
3. `backend-implementer` создаёт Alembic + начальную миграцию: `tenants`, `users`, `sites` с `tenant_id`; pgvector extension.
4. `devops-infra-specialist` настраивает 3 CI workflow + pre-commit.
5. `backend-implementer` подключает Celery + Redis (`ping` таска).
6. `backend-implementer` интегрирует PostHog Python SDK (stub-события).
7. `frontend-implementer` инициализирует Next.js 15 + PostHog JS SDK.
8. `compliance-152fz-specialist` ревьюит конфигурацию на предмет NFR-1 (данные только в RU, секреты вне кода).
9. Полный 5-линзовый аудит (`auditor`/Opus) — обязателен (tier 4).
