# REVIEW-REPORT · P1 (Foundation) · 2026-06-24

**Reviewer:** Sonnet-агент · **Вердикт: APPROVE-WITH-COMMENTS** (security-линза активна, tier-4).
**Диск-дифф:** `6e76dfd..62b654b` (60 файлов: backend + frontend + infra + CI).

Чистый, хорошо структурированный фундамент. Корректность solid (lifespan, async-сессии, lazy engine, async alembic env, celery, no-op аналитика). Multi-tenant `tenant_id` консистентно смоделирован и протестирован (реальный second-tenant isolation тест). Секретов в коде нет; РФ-резидентность на уровне валидации. CI гоняет реальные PG/pgvector/Redis/Celery/Keycloak как live-gold.

## Находки (диспозиция после цикла)

| severity | где | проблема | диспозиция |
|---|---|---|---|
| major | pyproject addopts + CI quality | coverage-гейт считается на unit-only подмножестве; integration job без `--cov-fail-under` | **fixed**: unit=86.81% (эмпирически ≥70); integration → `--no-cov` |
| minor | main.py middleware | CORS оказался внутренним (LIFO) | **fixed**: CORS вынесен внешним |
| minor | Caddyfile /metrics | Prometheus без auth публично | **fixed**: dev-only коммент (+ P9 prod-restrict) |
| minor | migrations/env.py | нет `compare_server_default` | **fixed**: добавлено |
| nit | db/base updated_at | ORM-only onupdate (нет DDL-триггера) | accept (документировано) |
| nit | frontend/.eslintrc.json | legacy config с eslint 9 | accept (миграция на flat — позже) |

## AC/FR coverage (reviewer)
- Covered: AC-3, AC-4, AC-6, AC-7, AC-8, FR-P1-2/3/4/5.
- Partial/deferred: AC-5 + FR-P1-1 «видно в PostHog UI» → DLG-1 (deferred_live_gold).
- Addressed-unverified-locally: AC-1 `make dev-bootstrap` ≤600с → DLG-2 (Docker нет в сессии).
- AC-2 ≥70%: **PASS** (86.81% unit).

## Top-3 (выполнено)
1. Разрешена coverage-неоднозначность (integration `--no-cov`). ✓
2. AC-5/FR-P1-1/AC-1 → явный deferred_live_gold в гейте. ✓
3. Middleware-порядок + `compare_server_default`. ✓
