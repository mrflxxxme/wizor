---
phase: P2
slug: crawler-audit
title: "Crawler / Аудит сайта (read-only)"
status: planned
tier: 3
track: read-only
depends_on: [P1]
gated_by: []
contracts: [crawler, scoring]
specialists: [crawler-probe-specialist]
prd_refs: [EPIC-1/FR-1.1, EPIC-1/FR-1.2]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Первая read-only продуктовая фаза. Краулер (Crawlee + Playwright) сканирует сайт и генерирует структурированный аудит-отчёт: robots.txt, sitemap, HTTP-коды, HTML-семантика, JSON-LD, FAQ-блоки, CWV, индексируемость (Bing/Я). Schema-валидатор (rdflib) проверяет JSON-LD. Нет записи на клиентский сайт. Результат: structured audit record в БД, готовый к передаче в P3 (Score). -->

## Goal

Реализовать read-only краулер сайта и schema-валидатор. По URL клиента собрать полный аудит Discovery + Comprehension слоёв и сохранить структурированный результат. Основание для P3 (Score) и всех последующих фаз.

## In scope

- **Crawlee (Python) + Playwright:** краул сайта до N страниц, обработка SPA (контент после JS-рендеринга).
- **Аудит-факторы (FR-1.1):** robots.txt (наличие + AI-боты разрешения), XML sitemap, HTTP-коды (2xx/3xx/4xx/5xx), HTML-семантика (h1–h3, article/section/nav/aside), наличие JSON-LD по типам (Organization, FAQPage, Article и др.), наличие FAQ-блоков (ответ-first паттерны), Core Web Vitals (через Lighthouse/PageSpeed API), индексируемость (Bing IndexNow статус + Яндекс.Вебмастер API).
- **Schema-валидатор (FR-1.2):** rdflib + custom JSON-LD validator — парсинг и валидация всех `<script type="application/ld+json">` на странице.
- **Celery-задача** `crawl_site(site_id, tenant_id)` — async, с ретраями (tenacity).
- **Хранение:** таблица `crawl_results` (tenant_id, site_id, crawled_at, pages_json, audit_summary_json, schema_validation_json).
- **Аудит конкурентов (stub):** структура данных готова для хранения конкурентного краула (реальный функционал → P6 FR-3.3).
- **Инвариант read-only:** нулевое взаимодействие с CMS клиента на запись.

## Out of scope

- AI-Readiness Score (→ P3).
- Probe LLM-моделей (→ P5).
- Генерация патчей/рекомендаций (→ P6).
- Re-crawl верификация (→ P8 / FR-5.5).
- Краул конкурентов полный (→ P6 / FR-3.3).

## Functional requirements

- **FR-1.1** Краулер сканирует сайт (Crawlee + Playwright для SPA): robots.txt, sitemap, HTTP-коды, структура HTML (h1–h3, semantic tags), наличие JSON-LD, наличие FAQ-блоков, Core Web Vitals, индексируемость (Bing/Я.Вебмастер).
  - **AC PRD:** для сайта до N страниц аудит завершается < T мин; формируется структурированный отчёт по каждому пункту с пометкой pass/warn/fail; обрабатываются SPA (контент после рендера).
- **FR-1.2** Schema-валидатор (rdflib + custom JSON-LD validator) проверяет корректность разметки до публикации.
  - **AC PRD:** невалидный JSON-LD не публикуется (→ активно в P10, но валидатор работает с P2); пользователь видит причину.

## Acceptance criteria

- **AC-1:** `crawl_site(site_id)` Celery-задача завершается успешно для тестового WP-сайта (≤100 страниц) за < 5 мин; все поля audit_summary_json заполнены (не `null`).
- **AC-2:** Каждый аудитируемый фактор (robots, sitemap, h1, JSON-LD, FAQ, CWV) имеет вердикт `pass` / `warn` / `fail` с текстовым пояснением.
- **AC-3:** SPA-тест: страница с client-side рендерингом (Playwright waiting) — контент корректно извлечён, `<h1>` найден после рендера.
- **AC-4:** Валидный JSON-LD → `schema_valid: true`; невалидный JSON-LD (намеренная ошибка в тесте) → `schema_valid: false` + поле `errors` с причиной.
- **AC-5:** `tenant_id` фильтрация: `SELECT * FROM crawl_results WHERE tenant_id != '<test>'` → 0 строк.
- **AC-6:** Сбой одной страницы (4xx) не роняет весь батч — остальные страницы обработаны.
- **AC-7:** Инвариант read-only подтверждён в аудите: ни одного HTTP PUT/POST/DELETE на клиентский сайт в логах.

## Contracts touched

- **`crawler` context:** `POST /internal/crawl` → Celery task; схема `crawl_results`; эмитирует событие `crawl.completed`. Стаб сейчас, `api.yaml` + `events.yaml` — JIT при планировании P2.
- **`scoring` context:** потребляет `crawl_results.audit_summary_json` (→ P3). Интерфейс — стаб.

## Exit-gate

| Критерий | Порог |
|---|---|
| Celery task success | ≤100 стр / 5 мин |
| Все audit-факторы | pass/warn/fail заполнен |
| SPA обработка | AC-3 пройден |
| JSON-LD валидатор | AC-4 пройден |
| Tenant изоляция | AC-5 пройден |
| Batch fault isolation | AC-6 пройден |
| Read-only инвариант | подтверждён аудитором (tier 3: 3 линзы) |

## Decomposition hints for planner

1. `crawler-probe-specialist` (Sonnet) проектирует и реализует Crawlee-паук + Playwright-рендеринг.
2. `backend-implementer` создаёт Celery-задачу `crawl_site`, Alembic-миграцию для `crawl_results`.
3. `crawler-probe-specialist` реализует schema-валидатор (rdflib парсинг + кастомные правила типов).
4. `backend-implementer` создаёт FastAPI эндпоинт `POST /api/v1/sites/{id}/crawl` → enqueue Celery.
5. `tester` пишет тесты: unit (парсинг HTML/JSON-LD fixtures), integration (реальный тестовый сайт).
6. `reviewer` проверяет read-only инвариант (нет write-операций на внешние сайты).
7. Аудит tier 3: correctness · security · compliance.
