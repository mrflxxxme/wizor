---
phase: P3
slug: readiness-score
title: "AI-Readiness Score (детерминированный)"
status: planned
tier: 3
track: read-only
depends_on: [P2]
gated_by: []
contracts: [scoring]
specialists: [geo-domain-expert]
prd_refs: [EPIC-1/FR-1.3, §3/принцип_2, §4.1, NFR-6]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Детерминированный scoring-движок поверх audit_summary из P2. Взвешенные факторы Discovery+Comprehension → единый Score [0–100] с компонентами. Ключевой инвариант: llms.txt НЕ входит в citation-вес. geo-domain-expert задаёт веса. Score воспроизводим: одинаковый вход → одинаковый выход. Readiness-проекция — детерминированная (что изменится после каждого фикса). -->

## Goal

Реализовать детерминированный движок расчёта AI-Readiness Score поверх результатов краулера (P2). Score — единственная быстрая сигнальная метрика продукта, онбординг-хук для пользователя. Должен быть воспроизводим и понятен.

## In scope

- **Scoring-движок:** взвешенная сумма факторов Discovery + Comprehension; выход — `score [0–100]` + компоненты с весами.
- **Факторы и веса** (задаёт `geo-domain-expert`):
  - Discovery: robots.txt AI-разрешения, sitemap, HTTP-здоровье, CWV, IndexNow-статус.
  - Comprehension: JSON-LD типы (Organization, FAQPage, Article и др.), FAQ-блоки / answer-first, семантическая HTML-структура, entity-граф (`@id`-связи), recency-сигналы.
  - **`llms.txt` НЕ включён в citation-вес** (инвариант §6 charter, FR-1.3 AC, §7.1 PRD-корректировка).
- **Readiness-проекция (детерминированная):** для каждого фикса из рекомендаций вычислить прирост Score (`delta_score`). Метод: пересчёт Score с применённым патчем без реального краула.
- **Компоненты Score раскрыты** пользователю: вес, значение, вердикт по каждому фактору.
- **API:** `GET /api/v1/sites/{id}/score` → `{score, components[], projection[]}`.
- **pgvector:** embedding Score-вектора для будущего semantic search (стаб, NFR-6).

## Out of scope

- Visibility/Citation Score (→ P5, probe-dependent).
- Весовая калибровка по реальным citation-данным (→ итерация после P5/P8 данных).
- Сравнение с конкурентами (→ P6 / FR-3.3).
- llms.txt как citation-фактор (явно вне scope — инвариант).

## Functional requirements

- **FR-1.3** Расчёт AI-Readiness Score (детерминированный, on-site) по взвешенным факторам Discovery+Comprehension.
  - **AC PRD:** Score воспроизводим (одинаковый вход → одинаковый выход); **llms.txt НЕ входит в citation-вес**; компоненты Score раскрыты пользователю.

## Acceptance criteria

- **AC-1 (воспроизводимость):** при одинаковом `audit_summary_json` Score идентичен на любом кол-ве вызовов; детерминизм подтверждён тестом с 100 прогонами.
- **AC-2 (llms.txt excluded):** принудительный тест — сайт с отличным llms.txt, но плохим FAQ/schema → Score не превышает Score сайта без llms.txt, но с хорошим FAQ/schema. Автоматизированный тест фиксирует инвариант.
- **AC-3 (компоненты раскрыты):** `GET /score` возвращает `components[]` с полями `name`, `weight`, `value`, `verdict`, `description` для каждого фактора.
- **AC-4 (Readiness-проекция):** для каждой рекомендации из P6-стаба `projection[]` содержит `fix_id`, `delta_score`, `new_score`; пересчёт без краула.
- **AC-5 (граничные значения):** Score для пустого сайта (нет robots, нет JSON-LD) ≥ 0 и ≤ 10; Score для идеально оптимизированного тестового сайта ≥ 85.
- **AC-6 (tenant изоляция):** Score хранится с `tenant_id`; cross-tenant читать нельзя.

## Contracts touched

- **`scoring` context:** `score_results` таблица (site_id, tenant_id, score, components_json, projection_json, calculated_at); `GET /api/v1/sites/{id}/score`; эмит `score.calculated`. Стаб расширяется JIT.
- Зависит от: `crawler.crawl_results.audit_summary_json`.
- Раскрывает: `score`, `projection` для `recommendations` context (→ P6).

## Exit-gate

| Критерий | Порог |
|---|---|
| Детерминизм Score | 100/100 прогонов = идентичный Score |
| llms.txt-инвариант | AC-2 тест пройден |
| Компоненты | все факторы в ответе с весами |
| Проекция | delta_score для каждого фикса |
| Граничные значения | AC-5 пройден |
| Аудит tier 3 | PASS (3 линзы: correctness · security · compliance) |

## Decomposition hints for planner

1. `geo-domain-expert` (Opus) — задаёт веса факторов, ревьюит формулу Score, подтверждает исключение llms.txt.
2. `backend-implementer` реализует `ScoringEngine` (pure function: `audit_summary → ScoreResult`).
3. `backend-implementer` создаёт Alembic-миграцию `score_results` + FastAPI эндпоинт.
4. `backend-implementer` реализует `ProjectionEngine` (пересчёт Score для каждого фикса без краула).
5. `tester` пишет параметризованные тесты детерминизма + граничных значений + llms.txt-инварианта.
6. `reviewer` проверяет отсутствие llms.txt в формуле (critical invariant check).
7. Аудит tier 3: correctness · security · compliance (инвариант llms.txt — отдельная пункт в чек-листе).
