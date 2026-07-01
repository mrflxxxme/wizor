# AUDIT-REPORT · P1 (Foundation) · 2026-06-24

**Auditor:** Opus-агент (адверсариальный) · **Tier:** 4 → 5 линз · **Ветка:** `claude/quirky-allen-meae1a`
**Вердикт: PASS-WITH-FIXES** (блокеров нет; фиксы применены в цикле / отложены в P9).

Линзы: корректность · security · compliance · тесты · архитектура. Фундамент крепкий: чистый bounded-context layout, честный no-op аналитики, реальная 152-ФЗ-валидация региона, multi-tenant с FK+индексом+изоляционным тестом, живой smoke в CI.

## Invariant check (charter §6) — 10/10

| # | инвариант | статус P1 | замечание |
|---|---|---|---|
| 1 | Read-only-граница | **PASS** | Нет продуктовых эндпоинтов; ноль write/API-вызовов (grep). |
| 2 | Honest forecast | N/A | Нет scoring в P1. |
| 3 | Auto-fix safety | N/A | Нет autofix; `seed()` идемпотентен (хороший прецедент). |
| 4 | Probe-гео (ноль РФ-IP) | N/A | Нет probe/внешних LLM (grep пусто). |
| 5 | llms.txt вне score | N/A | Нет scoring. |
| 6 | ПДн-резидентность РФ | **PASS** | `_enforce_ru_residency` (только ru-central1); 2 теста reject; compose форсит регион. |
| 7 | Uncertainty N≥5+CI | N/A | Нет метрик. |
| 8 | Multi-tenant изоляция | **PASS** | `tenant_id` (nullable=False, index) + FK CASCADE; миграция↔модели совпадают; integration-тест доказывает не-протекание. |
| 9 | Секреты не в коде | **PASS** | Нет committed `.env`; realm без secret; gitleaks+trivy+detect-private-key. |
| 10 | FAQ не авто-применяется | N/A | Нет recommendations/autofix. |

Критичные BLOCKED-триггеры (1/3/9) — чисты.

## Находки (5 линз) и диспозиция

| линза | severity | где | проблема | диспозиция |
|---|---|---|---|---|
| Корректность | minor | main.py /metrics | bare `/metrics` → 307 на `/metrics/` | **fixed-in-loop** (добавлен smoke-тест с follow_redirects) |
| Корректность | minor | worker/celery_app.py | `get_settings()` на import | accept (consistent, omit из cov) |
| Security | minor | keycloak realm | широкие флоу клиента skeleton | **defer-to-P9** (сузить при полной auth) |
| Security | minor | main.py + Caddyfile /metrics | /metrics без auth публично | **fixed-in-loop** (dev-only коммент) + defer-to-P9 (prod restrict) |
| Security | info | CORS | allow_credentials + ["*"] | accept (origins — явный список, не `*`; антипаттерн не применяется) |
| Compliance | — | — | чисто | — |
| Тесты | minor | CI coverage | unit/integration раздельные cov | **fixed-in-loop** (integration `--no-cov`; unit gate 86.8%) |
| Тесты | info | deferred PostHog/bootstrap | честный deferral | accept (ADR-0018) |
| Архитектура | info | вся src | чистый layout, файлы <500, lazy engine | accept |

## Reviewer-находки (см. REVIEW-REPORT.md) — диспозиция
- major (coverage-гейт неоднозначность) → **fixed-in-loop**: эмпирически unit=86.81%; integration переведён на `--no-cov`.
- minor middleware-порядок → **fixed-in-loop**: CORS вынесен внешним.
- minor `compare_server_default` → **fixed-in-loop**: добавлено в alembic env.
- AC-5/FR-P1-1/AC-1 deferred → зафиксировано в гейте (DLG-1/DLG-2).

## Что должно быть пофикшено до авто-мерджа
**Ничего** (нет blocker/major после цикла фиксов). P1 готов к founder-гейту.

## P9-рекомендации (отложены)
- Сузить флаги Keycloak-клиента при реальной auth.
- Закрыть `/metrics` от публичного доступа на проде.
