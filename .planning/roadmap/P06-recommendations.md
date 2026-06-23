---
phase: P6
slug: recommendations
title: "Рекомендации + competitive gap + патчи + honest forecast"
status: planned
tier: 3
track: read-only
depends_on: [P3, P5]
gated_by: []
contracts: [recommendations, patches]
specialists: [geo-domain-expert, crawler-probe-specialist]
prd_refs: [EPIC-3/FR-3.1, EPIC-3/FR-3.2, EPIC-3/FR-3.3, EPIC-3/FR-3.4, EPIC-3/FR-3.5]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Read-only фаза. Реализует полный движок рекомендаций: приоритизированный список фиксов с impact-прогнозом, FAQ-генератор (answer-first, RU-default, только draft), конкурентный gap-анализ (краул цитируемых конкурентов), copy-paste патчи для Manual track, честный прогноз (Readiness-проекция детерминированно + Visibility только диапазоном). Все рекомендации read-only — никакой записи на сайт клиента. -->

## Goal

Реализовать движок рекомендаций, который превращает результаты Score (P3) и Probe (P5) в конкретные actionable фиксы: приоритизированный список, конкурентный gap, copy-paste патчи для Manual track, FAQ-драфты на ревью, честный прогноз без гарантированных процентов.

## In scope

- **Прио-лист фиксов (FR-3.1):** ранжирование по `impact_score = delta_score × citation_potential`; каждый фикс помечен: тип (`machine_readable` / `content`), канал применения (`auto` / `review` / `manual-paste`).
- **FAQ-генератор answer-first (FR-3.2):** через LLM-router (RU-default → GigaChat/YandexGPT); 50–150 слов; FAQ всегда статус `draft`, никогда не публикуется без явного подтверждения (инвариант §6.10 + FR-4.2 AC).
- **Competitive gap analysis (FR-3.3):** краул конкурентов, которых LLM цитирует по целевым промптам; для каждого промпта — список cited-источников + конкретные структурные отличия (schema-типы, FAQ-наличие, answer-first паттерны) vs сайт клиента.
- **Copy-paste патчи для Manual track (FR-3.4):** самодостаточный артефакт на каждый фикс: JSON-LD snippet, строки robots.txt, контент llms.txt, FAQ-HTML блок + инструкция «куда вставить». Доступны без API.
- **Прогноз честный (FR-3.5):** Readiness-проекция (детерминированно) — «после этих фиксов Score X→Y»; competitive gap — доказательное сравнение без выдуманных %; Visibility-прогноз — только диапазон+доверие+индустриальные бенчмарки, помечен как оценка. **Нигде не показывается гарантированный Visibility-%.**
- **Валидатор патчей:** JSON-LD-сниппеты проходят через валидатор (P2/FR-1.2) до попадания в артефакт.

## Out of scope

- Авто-применение патчей (→ P10 / EPIC-4).
- Re-crawl верификация применённого (→ P8 / FR-5.5).
- FAQ авто-публикация (→ P10, только через review-flow FR-4.3).
- Sentiment-анализ (→ фаза B).
- PDF/PPTX отчёты (→ фаза B).
- Предиктивная site-specific Visibility-модель (→ roadmap-айтем после Auto track накопит данные).

## Functional requirements

- **FR-3.1** Генерация прио-листа фиксов с прогнозом impact и пометкой «авто-применимо / требует review».
  - **AC PRD:** топ-фиксы отсортированы по ожидаемому impact; для каждого — тип и канал применения.
- **FR-3.2** FAQ-генератор (answer-first, 50–150 слов) через LLM-router (RU-default); FAQ = draft, не публикуется без review.
  - **AC PRD:** FAQ помечается как **draft**; не публикуется без review.
- **FR-3.3** Competitive gap: краул цитируемых конкурентов; сравнение Readiness/структуры; вывод разрыва как evidence.
  - **AC PRD:** для каждого целевого промпта — cited-источники + структурные отличия; без выдуманных %.
- **FR-3.4** Copy-paste патчи: JSON-LD snippet, robots.txt строки, llms.txt контент, FAQ-блок + инструкция. Доступны без API.
  - **AC PRD:** артефакт валиден и самодостаточен; доступен без write-доступа.
- **FR-3.5** Прогноз: Readiness-проекция (детерминированно) + competitive gap + Visibility только диапазоном с доверием.
  - **AC PRD:** нигде нет гарантированного Visibility-%; вероятностные прогнозы помечены + доверительный диапазон.

## Acceptance criteria

- **AC-1 (прио-лист):** `GET /api/v1/sites/{id}/recommendations` возвращает ≥3 фикса, отсортированных по `impact_score` DESC; у каждого `type` и `apply_channel`.
- **AC-2 (FAQ draft):** сгенерированный FAQ имеет `status: draft`; попытка опубликовать без `review_approved: true` → 422 ошибка. Тест фиксирует инвариант.
- **AC-3 (competitive gap):** для промпта с ≥1 cited-конкурентом в БД — ответ содержит `cited_competitors[]` с полями `url`, `schema_types[]`, `has_faq`, `has_answer_first`; у клиента те же поля для сравнения.
- **AC-4 (copy-paste патч):** JSON-LD-артефакт из рекомендации проходит schema-валидатор (FR-1.2) без ошибок.
- **AC-5 (honest forecast):** при любом вызове `GET /recommendations` поле `visibility_forecast` содержит `range_low`, `range_high`, `confidence`, `disclaimer`; поле `visibility_guarantee` отсутствует в схеме (тест на schema-validate).
- **AC-6 (Manual track):** вся цепочка аудит→рекомендации→патчи работает без write-доступа к сайту клиента (тест: mock-сайт без CMS-коннектора → полный набор рекомендаций получен).
- **AC-7 (FAQ длина):** сгенерированный FAQ ≥ 50 и ≤ 150 слов (тест с deterministic mock LLM).

## Contracts touched

- **`recommendations` context:** `recommendations` таблица (site_id, fix_type, apply_channel, impact_score, patch_artifact_id, status); `competitor_gaps` таблица; `GET /api/v1/sites/{id}/recommendations`.
- **`patches` context:** `patch_artifacts` таблица (fix_id, artifact_type, content, validated_at, validation_ok); `GET /api/v1/patches/{id}`.
- Зависит от: `scoring.score_results` (P3), `metrics.visibility_metrics` (P5), `probe.probe_runs` (P5).
- Раскрывает: `recommendations[]` и `patch_artifacts[]` для `autofix` (P10) и `verification` (P8).

## Exit-gate

| Критерий | Порог |
|---|---|
| Прио-лист с impact | AC-1 (≥3 фикса, отсортировано) |
| FAQ draft-only инвариант | AC-2 (422 без review) |
| Competitive gap | AC-3 (cited_competitors с деталями) |
| Патч валидация | AC-4 (0 schema-ошибок) |
| Honest forecast | AC-5 (нет `visibility_guarantee`) |
| Manual track без API | AC-6 пройден |
| Аудит tier 3 | PASS (3 линзы: correctness · security · compliance) |

## Decomposition hints for planner

1. `geo-domain-expert` (Opus) задаёт impact-формулу, приоритеты фиксов, правила competitive gap.
2. `crawler-probe-specialist` (Sonnet) реализует краул cited-конкурентов (из probe-данных P5).
3. `backend-implementer` создаёт `RecommendationEngine` (Score + probe → прио-лист), Alembic-миграции.
4. `backend-implementer` интегрирует LLM-router для FAQ-генерации (RU-default, draft-only).
5. `backend-implementer` реализует `PatchArtifactBuilder` + интеграцию schema-валидатора.
6. `backend-implementer` создаёт FastAPI эндпоинты (recommendations, patches).
7. `tester` пишет тесты: FAQ-draft инвариант, honest forecast (нет guarantee), Manual track без API.
8. Аудит tier 3: correctness (прогноз без гарантий) · security · compliance (ПД в FAQ, RU-модели).
