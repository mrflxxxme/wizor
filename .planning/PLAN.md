<!-- HEAD-SUMMARY (≤500т): Pinned-план фазы P2 (Crawler/Аудит, read-only, tier 3), составлен по методологии (ADR-0021 discuss→plan). Read-only краулер Crawlee+Playwright + schema-валидатор rdflib + Celery-задача crawl_site + таблица crawl_results + FastAPI enqueue-эндпоинт. Front-autonomy (D4): 8 форков разобрано → 8 owned+logged, **0 блокирующих эскалаций** (1 deferred product-note: per-tariff crawl-caps → P9). Migration crawl_results = tripwire db_migrations на мёрже (ack v1 / greenfield-nuance). Specialist: crawler-probe-specialist (Sonnet). Live-gold: crawl golden против тест-WP. -->

# PLAN — P2 Crawler / Аудит (read-only)

> **Источник:** `roadmap/P02-crawler-audit.md` · контракты `crawler`, `scoring`. **Составлен:** 2026-07-03 discuss-шаг (ADR-0021 D4). **Pinned** — без переобдумывания на ходу (charter §4 шаг 2).
> **Tier 3** → аудит 3 линзы (correctness · security · compliance); CI полный; live-gold crawl обязателен (ADR-0018).

## Front-autonomy: разбор форков (D4)

Агент **владеет** всеми impl+arch форками (decide+log); эскалирует только продукт/рынок + tripwire (`escalation-policy.md`). Итог: **8 owned+logged, 0 блокирующих эскалаций.**

| # | Форк | Класс | Решение (owned) |
|---|---|---|---|
| 1 | Crawl-движок | impl (стек залочен ADR-0011) | Crawlee-Python + Playwright для SPA-рендера |
| 2 | Глубина/таймаут краула | impl (+deferred product-note) | Конфигурируемый cap, дефолт 100 стр / 5 мин (AC-1). **Per-tariff лимиты (Tier0/Manual/Auto) — product → P9**, не блокирует P2 |
| 3 | Хранение страниц | **wide arch** | Извлечённые сигналы + content-hash per page (не полный HTML-блоб): достаточно для P8 re-crawl delta, дешевле, без лишних ПДн. Полный снапшот — только по флагу |
| 4 | CWV-источник | arch (+placeholder) | Pluggable adapter; дефолт — stub-verdict `deferred`; реальный (PageSpeed API / local Lighthouse) — когда founder даст ключ (PLACEHOLDERS). CWV — минорный citation-фактор (подтвердить с geo в P3) |
| 5 | Индексируемость Bing/Яндекс | arch (+placeholder) | Pluggable adapter; дефолт stub; реальный при наличии creds (PLACEHOLDERS) |
| 6 | Вердикты pass/warn/fail | domain (geo-методология) | Факт-уровневые пороги как разумные дефолты; **веса Score — P3/geo**, здесь только флаги фактора |
| 7 | Read-only enforcement (§6 инв.1) | **arch, high-stakes** | Жёсткий guard: HTTP-клиент краулера — только GET; не-GET к внешнему домену → raise + audit-log. Тест AC-7 ассертит ноль PUT/POST/DELETE |
| 8 | Схема `crawl_results` | arch (migration=tripwire@merge) | Одна таблица, tenant_id+FK+index (§6.8), JSONB-поля pages/audit_summary/schema_validation. Greenfield CREATE через `_rls` literal-хелперы → classify авто-снимет db_migrations |

**Escalations:** нет блокирующих. **Deferred product-note:** per-tariff crawl-caps (#2) → founder-решение на P9 (billing). **Tripwire@merge:** миграция `crawl_results` (#8) — db_migrations; greenfield-CREATE → classify_tripwire content-check авто-снимет, иначе 1-клик `/ack`.

## Задачи (атомарные · pinned)

| id | role | tier/model | AC | contracts | depends | wide_fork |
|---|---|---|---|---|---|---|
| T1 | crawler-probe-specialist | 3/Sonnet | Crawlee-паук + Playwright SPA-рендер; read-only GET-guard (#7); N-cap config | crawler | — | — |
| T2 | backend-implementer | 3/Sonnet | Alembic-миграция `crawl_results` (greenfield CREATE + tenant-RLS через `_rls`) | crawler | — | — |
| T3 | crawler-probe-specialist | 3/Sonnet | Извлечение аудит-факторов (robots/sitemap/HTTP/h1-h3/JSON-LD/FAQ) + вердикты pass/warn/fail (AC-2) | crawler | T1 | — |
| T4 | crawler-probe-specialist | 3/Sonnet | Schema-валидатор rdflib + custom JSON-LD правила (AC-4) | crawler | T1 | — |
| T5 | crawler-probe-specialist | 3/Sonnet | CWV + индексируемость как pluggable adapters (дефолт stub-deferred; #4/#5) | crawler | T3 | ✓ (adapter-seam) |
| T6 | backend-implementer | 3/Sonnet | Celery `crawl_site(site_id, tenant_id)` + tenacity retries; batch fault-isolation (AC-6) | crawler | T1,T2,T3,T4 | — |
| T7 | backend-implementer | 3/Sonnet | FastAPI `POST /api/v1/sites/{id}/crawl` → enqueue; событие `crawl.completed`; api.yaml+events.yaml JIT | crawler | T6 | — |
| T8 | crawler-probe-specialist | 3/Sonnet | Тесты: unit (HTML/JSON-LD фикстуры, SPA AC-3, tenant AC-5), + live-gold crawl golden | crawler | T3–T7 | — |

**Специалист (mode B, charter §4 шаг 3):** `crawler-probe-specialist` сам пишет код домена (T1/T3/T4/T5/T8); `backend-implementer` — Celery/миграция/эндпоинт (T2/T6/T7). Спавн — `load_role.py --role <role>`.

## Гейты (шаги 5–7)
- **Review:** `reviewer` — фокус read-only инвариант (#7, AC-7), tenant-изоляция (AC-5); security-линза (внешние HTTP).
- **Verify (ADR-0018):** unit+integration coverage ≥70%; **live-gold:** `crawl_site` против founder-owned тест-WP (≤100 стр / 5 мин, AC-1) → `evidence/live_golden_crawl.json` + `evidence/manifest.json {"phase":"P2","required_gates":["live_golden_crawl","adversarial_audit"]}`. Нет тест-WP → `deferred_live_gold` в гейт.
- **Audit (tier 3):** correctness · security · compliance + 10 инвариантов §6 (критично: #1 read-only, #8 tenant) → `evidence/adversarial_audit.json`.

## Exit-gate (из phase-spec)
Celery success ≤100стр/5мин · все факторы pass/warn/fail · SPA (AC-3) · JSON-LD валидатор (AC-4) · tenant (AC-5) · batch fault-isolation (AC-6) · read-only подтверждён аудитором (AC-7).

## Live-gold placeholder-зависимости (founder)
- Тест-WP URL для crawl golden (AC-1) — иначе `deferred_live_gold`.
- (Опц., не блокирует P2) PageSpeed API key + Bing/Яндекс creds для реальных CWV/индексируемости (#4/#5); до этого — stub-adapters.
