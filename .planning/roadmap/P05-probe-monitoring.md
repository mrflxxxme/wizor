---
phase: P5
slug: probe-monitoring
title: "Probe-мониторинг (dual-geo, N≥5+CI)"
status: planned
tier: 3
track: read-only
depends_on: [P4]
gated_by: []
contracts: [probe, metrics]
specialists: [crawler-probe-specialist, llm-router-specialist]
prd_refs: [EPIC-2/FR-2.1, EPIC-2/FR-2.2, EPIC-2/FR-2.3, EPIC-2/FR-2.4, §9.3/NFR-2, §9.3/NFR-5]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Read-only фаза. Реализует probe-мониторинг 4 LLM-моделей (ChatGPT, Perplexity, Алиса/Нейро, GigaChat) с дуал-гео (RU API для RU-моделей, зарубежные ноды для иностранных). Каждый промпт N≥5 прогонов, агрегация с CI. Метрики: Visibility Score (композит), Coverage/Presence, Share of Voice, Citation Rate, Stability. Celery async batch. Данные — основа для P6 (рекомендации) и P8 (верификация). -->

## Goal

Реализовать систему probe-мониторинга: автоматический запрос 4 LLM-моделей по целевым промптам пользователя, N≥5 прогонов с доверительным интервалом, хранение сырых ответов и агрегированных метрик. Все probe к иностранным моделям — через зарубежные ноды (инвариант §6).

## In scope

- **Гибридный набор промптов (FR-2.1):** авто-генерация 20–30 кандидатов из сущностей/тем сайта (через LLM-router RU-модель); пользователь правит/добавляет/удаляет; набор версионируется.
- **4 LLM-модели (FR-2.2):**
  - Алиса/Нейро → Yandex Cloud Foundation Models API (RU-нода, РФ).
  - GigaChat → GigaChat API (RU-нода, РФ).
  - ChatGPT → OpenAI API через зарубежную ноду (Hetzner/Selectel) + резидентный прокси.
  - Perplexity → Perplexity API через зарубежную ноду + резидентный прокси.
- **Dual-geo архитектура:** RU-ноды для RU-моделей; зарубежные ноды (Hetzner/Selectel) + прокси для ChatGPT/Perplexity. **Ни один запрос к ChatGPT/Perplexity не с РФ-IP** (инвариант §6.4).
- **N≥5 прогонов (FR-2.3):** каждый промпт × каждая модель → ≥5 независимых вызовов; результаты агрегируются; доверительный интервал (CI) / полоса стабильности вычисляется.
- **Метрики (FR-2.4):** Visibility Score (композит), Coverage/Presence (% промптов с упоминанием), Share of Voice (% ответов с упоминанием vs конкуренты), Citation Rate (процитирован как источник/дана ссылка), Stability (дисперсия между прогонами).
- **Celery + Redis async batch** (NFR-5): probe-батч — асинхронный; сбои отдельных вызовов логируются, не роняют батч.
- **Retry/ротация прокси** (FR-2.2 AC): httpx + tenacity + ротация proxy-pool.
- **Evidence-захват (стаб):** raw ответы хранятся → используются в P8 (FR-5.3).
- **Scraping fallback** (§12): если нет API — веб-скрапинг через зарубежную ноду.

## Out of scope

- Алерты деградации (→ P8 / FR-5.4).
- Velocity-сдвиги / верификация до/после (→ P8 / FR-5.2).
- Evidence-скриншоты (→ P8 / FR-5.3 полная реализация).
- DeepSeek/Claude в probe (→ A.4, вне MVP scope).
- Sentiment-трекинг (→ фаза B).

## Functional requirements

- **FR-2.1:** гибридный набор промптов (авто-ген + курирование), версионируется.
  - **AC PRD:** пользователь получает готовый набор при онбординге за < T; может редактировать; набор версионируется.
- **FR-2.2:** Probe dual-geo (RU-API для RU, зарубежные ноды для ChatGPT/Perplexity); retry/ротация прокси; сбои логируются, батч не роняется.
  - **AC PRD:** ни один probe к ChatGPT/Perplexity не идёт с РФ-IP; retry настроен; сбои логируются.
- **FR-2.3:** N≥5 прогонов на промпт; CI/полоса стабильности.
  - **AC PRD:** для каждой метрики хранится распределение по прогонам и CI.
- **FR-2.4:** Метрики Visibility + Coverage + SoV + Citation Rate + Stability; UI: Score + 4 компонента с полосой шума.
  - **AC PRD:** UI показывает Score + 4 компонента с полосой шума; сырые распределения доступны по запросу.

## Acceptance criteria

- **AC-1:** Celery-задача `run_probe_batch(site_id)` для 10 промптов × 4 модели × 5 прогонов = 200 LLM-вызовов завершается без падения всего батча при ≤10% ошибок.
- **AC-2 (dual-geo инвариант):** тест с mock-прокси: все вызовы ChatGPT/Perplexity через `PROXY_FOREIGN` переменную; прямого RU-IP нет (проверяется assertions в тестах и log-audit).
- **AC-3 (N≥5):** для любого промпта в БД хранится ≥5 raw-ответов с временными метками; агрегат содержит `mean`, `ci_lower`, `ci_upper`.
- **AC-4 (метрики):** `GET /api/v1/sites/{id}/visibility` возвращает `{visibility_score, components: {coverage, sov, citation_rate, stability}, ci_lower, ci_upper}`.
- **AC-5 (промпт-версионирование):** изменение набора промптов создаёт новую версию; исторические probe привязаны к старой версии.
- **AC-6 (fault isolation):** при 100% ошибках одного провайдера (mock) — остальные 3 провайдера обрабатываются успешно; ошибка логируется как `provider_failed`, не как `batch_failed`.
- **AC-7 (Stability):** Stability-метрика > 0.8 для детерминированного mock-провайдера (одинаковые ответы → низкая дисперсия).

## Contracts touched

- **`probe` context:** `probe_runs` таблица (site_id, tenant_id, prompt_id, model, run_at, raw_response, cited, mentioned); `prompt_sets` таблица (версионирование). `POST /internal/probe/run` → Celery.
- **`metrics` context:** `visibility_metrics` (агрегат по site/period); `GET /api/v1/sites/{id}/visibility`.
- Зависит от: `llm-router` (P4).
- Раскрывает: raw-данные для `verification` (P8); агрегат для `recommendations` (P6).

## Exit-gate

| Критерий | Порог |
|---|---|
| Batch 200 вызовов | без падения при ≤10% ошибок |
| Dual-geo инвариант | AC-2 (0 RU-IP для иностранных) |
| N≥5 + CI | AC-3 для каждого промпта |
| 4 метрики | AC-4 в ответе API |
| Fault isolation | AC-6 (1 провайдер падает → 3 продолжают) |
| Аудит tier 3 | PASS (3 линзы: correctness · security · compliance) |

## Decomposition hints for planner

1. `crawler-probe-specialist` (Sonnet) реализует probe-клиенты для 4 моделей + proxy-routing.
2. `crawler-probe-specialist` реализует retry/ротацию прокси (httpx + tenacity).
3. `backend-implementer` создаёт Celery-задачу `run_probe_batch`, Alembic-миграции.
4. `llm-router-specialist` интегрирует probe-канал роутера (dual-geo routing правила).
5. `backend-implementer` реализует агрегацию метрик (mean, CI, Stability).
6. `backend-implementer` создаёт FastAPI эндпоинты (visibility + prompt management).
7. `tester` пишет тесты: dual-geo инвариант (mock-прокси), fault-isolation, N≥5, CI-агрегация.
8. Аудит tier 3: correctness · security · compliance (фокус: dual-geo + ПД в raw-ответах).
