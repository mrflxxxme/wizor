# AUDIT · P3 · линза SECURITY · 2026-07-05

## Multi-tenant изоляция (§6.8) — PASS
- `tenant_id` берётся из `request.state` (`router.py:62`, `get_tenant_id`), НИКОГДА из тела DTO.
  Без `X-Tenant-Id` → 400 (`router.py:63-67`).
- Все запросы репозитория tenant-scoped:
  - `load_latest_crawl` — `WHERE tenant_id AND site_id` (`repository.py:33-41`).
  - `load_site_url` — `WHERE id AND tenant_id` (`repository.py:53`).
  - `save_score_result` — `tenant_id` из kwargs контекста, не из `ScoreResult` DTO
    (`repository.py:58-83`).
- Гейт `load_latest_crawl` до записи гарантирует: строка score_results создаётся только для
  сайта, у которого есть краул этого тенанта → сайт принадлежит тенанту (app-level изоляция;
  Postgres RLS — план P9, консистентно с charter/tenancy.py).
- Integration `test_tenant_isolation_ac6`: чужой tenant+site+score вставлен; scoped-select по
  TEST не видит чужую строку, `WHERE tenant_id != TEST` не возвращает строку TEST. **PASS.**

## Secrets (§6.9) — PASS
- Scoring — чистый compute; секретов нет. Grep диффа по `password|secret|api_key|token|aws_|
  PRIVATE|sk-|ghp_|bearer` → ноль совпадений в `+`-строках.

## SQL-инъекции / DDL — PASS
- Продакшн-репозиторий: только параметризованный SQLAlchemy `select()`; f-string/`.format()`
  в SQL отсутствуют.
- Миграция: `op.create_table` (статичный DDL), без f-string DDL-циклов.
- `Vector.get_col_spec` = `f"vector({self.dim})"`, `self.dim` — константа `EMBEDDING_DIM=1536`
  (int, не пользовательский вход) → не инъектируемо.
- Raw `text()` встречается только в integration-тестах и с bound-параметрами.

## Auth / поверхность эндпоинта
- Аутентификация (JWT/Keycloak) — P9 по роадмапу; в P3 tenancy = header-skeleton (по дизайну,
  не регресс). `site_id` path-валидируется FastAPI (422 на невалидный UUID). N-A для P3.

**Вывод линзы: PASS.**
