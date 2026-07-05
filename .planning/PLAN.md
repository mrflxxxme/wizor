<!-- HEAD-SUMMARY (≤500т): Pinned-план фазы P3 (AI-Readiness Score, read-only, tier 3), составлен методологией (ADR-0021 discuss→plan). Детерминированный ScoringEngine поверх crawl_results.audit_summary_json (P2) → score[0–100] + раскрытые компоненты + Readiness-проекция (delta_score без краула). geo-domain-expert (Opus) задаёт веса факторов. Критический инвариант §6.5: **llms.txt НЕ в citation-весе** (AC-2 форсит тестом). Front-autonomy: 7 форков → 7 owned, **0 эскалаций** (веса = geo-домен, не продукт; llms.txt-исключение = граница, не форк). Migration score_results = tripwire db_migrations на мёрже. Specialists: geo-domain-expert (веса) + backend-implementer (движок). -->

# PLAN — P3 AI-Readiness Score (детерминированный)

> **Источник:** `roadmap/P03-readiness-score.md` · контракт `scoring` · вход `crawler.crawl_results.audit_summary_json` (P2, на main). **Составлен:** 2026-07-05 discuss (ADR-0021 D4). **Pinned.**
> **Tier 3** → аудит 3 линзы; **llms.txt-инвариант (§6.5) — отдельный пункт аудит-чек-листа**.

## Front-autonomy: разбор форков (D4)

**7 форков → 7 owned+logged, 0 блокирующих эскалаций.** Веса Score = geo-домен-методология (owned per escalation-policy; НЕ продукт — набор факторов уже зафиксирован PRD FR-1.3). llms.txt-исключение — стоячий инвариант §6.5, граница, не форк.

| # | Форк | Класс | Решение (owned) |
|---|---|---|---|
| 1 | Формула Score | domain (geo) | Взвешенная линейная сумма нормированных факторов → [0–100]; веса задаёт geo-domain-expert |
| 2 | Веса факторов | **domain (geo, Opus)** | geo-domain-expert выдаёт версионированную карту вес×фактор (Discovery+Comprehension) + обоснование; **llms.txt отсутствует структурно** |
| 3 | Детерминизм | arch | Чистая функция `audit_summary → ScoreResult`; веса — версионированная константа (смена формулы = новая версия, не мутация истории) |
| 4 | Readiness-проекция | arch | `ProjectionEngine`: применяет патч к audit_summary в памяти → пересчёт Score без краула → `delta_score` per fix (AC-4) |
| 5 | Схема `score_results` | arch (migration=tripwire@merge) | tenant_id+FK+index (§6.8), JSONB components/projection, score_version; greenfield CREATE |
| 6 | pgvector Score-embedding | arch (stub, NFR-6) | Колонка/стаб под будущий semantic search; не вычисляется в P3 |
| 7 | Версионирование весов | arch | `score_version` в результате + константа весов; тест AC-1 привязан к версии |

**Escalations:** нет. **Tripwire@merge:** миграция `score_results` → db_migrations (greenfield → classify авто-снимет / 1-клик ack).

## Задачи (атомарные · pinned)

| id | role | tier/model | AC | contracts | depends |
|---|---|---|---|---|---|
| T1 | geo-domain-expert | 3/**Opus** | Карта весов Discovery+Comprehension + формула + **структурное исключение llms.txt** + обоснование; версия весов | scoring | — |
| T2 | backend-implementer | 3/Sonnet | `ScoringEngine` — чистая fn `AuditSummary → ScoreResult` (score + components[name,weight,value,verdict,description], AC-1/AC-3) | scoring | T1 |
| T3 | backend-implementer | 3/Sonnet | Alembic `score_results` + модель (TenantMixin §6.8) + pgvector-стаб | scoring | — |
| T4 | backend-implementer | 3/Sonnet | `ProjectionEngine` — delta_score per fix без краула (AC-4) | scoring | T2 |
| T5 | backend-implementer | 3/Sonnet | `GET /api/v1/sites/{id}/score` → {score, components[], projection[]} + событие `score.calculated`; читает crawl_results | scoring | T2,T3 |
| T6 | backend-implementer | 3/Sonnet | Тесты: детерминизм 100× (AC-1), **llms.txt-инвариант (AC-2)**, компоненты (AC-3), проекция (AC-4), границы 0–10/≥85 (AC-5), tenant (AC-6) | scoring | T2–T5 |

**Domain (mode B):** `geo-domain-expert` (Opus) — T1 (веса — never-fallback, судительная задача). `backend-implementer` — T2–T6 (движок детерминирован, чистые функции).

## Гейты
- **Review:** `reviewer` — **критический чек: llms.txt отсутствует в формуле/весах** (grep + логика); детерминизм; tenant (AC-6).
- **Verify (ADR-0018):** unit coverage ≥70%; детерминизм-тест 100 прогонов; **AC-2 llms.txt-инвариант**; границы AC-5. Live-gold: Score против golden audit_summary (детерминированный — не нужен внешний сервис; можно прогнать локально/в CI, НЕ deferred).
- **Audit (tier 3):** correctness · security · compliance + §6 (особенно #5 llms.txt, #8 tenant, #2 honest-forecast: проекция детерминирована, не «гарантия»).

## Exit-gate
Детерминизм 100/100 · llms.txt-инвариант AC-2 · компоненты раскрыты · проекция delta_score · границы AC-5 · audit tier-3 PASS.
