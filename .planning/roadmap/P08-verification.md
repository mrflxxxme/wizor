---
phase: P8
slug: verification
title: "Верификация (re-crawl, Visibility-delta, evidence, алерты)"
status: planned
tier: 3
track: read-only
depends_on: [P6]
gated_by: []
contracts: [verification, notifications]
specialists: [crawler-probe-specialist]
prd_refs: [EPIC-5/FR-5.1, EPIC-5/FR-5.2, EPIC-5/FR-5.3, EPIC-5/FR-5.4, EPIC-5/FR-5.5]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Read-only фаза. Замыкает цикл доказательств: Readiness-delta (быстро, детерминированно), Visibility/Citation-delta (медленно, с полосой шума), evidence-захват (скриншоты ответов ИИ), алерты деградации, re-crawl верификация применённого вручную (FR-5.5 — работает без API). Ключевой retention-аргумент продукта: «вот доказательство, что правки работают». -->

## Goal

Реализовать двухуровневую верификацию: (1) мгновенный Readiness-delta после применения правки; (2) медленный Visibility/Citation-delta по probe во времени с полосой шума; (3) захват evidence (скриншоты ответов ИИ); (4) алерты деградации; (5) re-crawl без API. Retention-доказательство для Manual track.

## In scope

- **Readiness-delta (FR-5.1):** после применения правки (auto или manual) — немедленный пересчёт Score + показ delta (`+12 пунктов из-за добавления FAQPage-schema`). Детерминированно, без краула.
- **Visibility/Citation-delta (FR-5.2):** повторные probe во времени; «реальный» сдвиг = выход за полосу шума (CI); тренд-график с полосой шума; система не заявляет улучшение внутри шума.
- **Evidence-захват (FR-5.3):** снапшот ответа ИИ (текст) + скриншот (Playwright) для каждого промпта × модели; хранение с датой, prompt_id, model_id; привязка к до/после точкам.
- **Алерты деградации (FR-5.4):** при падении метрики вне полосы шума → email + Telegram + webhook. Настраивается тенантом (каналы, пороги).
- **Re-crawl верификация без API (FR-5.5):** повторный краул публичных страниц клиента подтверждает, что патч из Manual track применён в HTML (schema/FAQ/robots/llms.txt присутствует). Score пересчитывается по фактическому HTML.

## Out of scope

- A/B-тестирование AI-видимости (→ фаза C).
- Сравнительный attribution (какая именно правка дала какой Visibility-сдвиг) — только observational, не causal.
- PDF/PPTX отчёты по evidence (→ фаза B).
- Prediction модель («когда увижу рост») → roadmap после Auto track накопит данные.

## Functional requirements

- **FR-5.1** Readiness-delta (быстро, детерминированно): после правки — прирост Score с указанием фикса.
  - **AC PRD:** после применения правки пользователь сразу видит прирост Score с указанием, какая правка дала.
- **FR-5.2** Visibility/Citation-delta (медленно): тренд probe во времени; «реальный» = вне шума.
  - **AC PRD:** тренд показывается с полосой шума; система не заявляет улучшение внутри шума.
- **FR-5.3** Evidence-захват: снапшоты ответов ИИ до/после с датой и привязкой к промпту/модели.
  - **AC PRD:** снапшоты сохраняются с датой и привязкой к промпту/модели.
- **FR-5.4** Алерты деградации: при падении метрики вне шума → email/Telegram/webhook.
  - **AC PRD:** при падении метрики вне полосы шума отправляется алерт.
- **FR-5.5** Re-crawl верификация (Manual track): краул HTML → детект наличия патча → Readiness-delta без API.
  - **AC PRD:** система детектирует факт применения без API; Readiness-delta пересчитывается по фактическому состоянию HTML.

## Acceptance criteria

- **AC-1 (Readiness-delta):** `POST /api/v1/sites/{id}/verify/readiness` после добавления FAQPage-schema вручную → ответ содержит `delta: +N`, `reason: "FAQPage schema detected"`, `new_score: X`.
- **AC-2 (Visibility-delta — no false positives):** тест с mock-данными: если Δ visibility < CI half-width → `is_significant: false`; только при Δ > CI → `is_significant: true`. Тест фиксирует инвариант «нет ложных побед».
- **AC-3 (Evidence):** после probe-прогона скриншот Playwright сохранён в `evidence_snapshots` (site_id, prompt_id, model, captured_at, image_path); `image_path` существует (file check).
- **AC-4 (Алерт):** при Mock-падении метрики Visibility за полосу шума — в тестовом окружении email-адаптер вызван (mock assert), Telegram-адаптер вызван; `notification_log` содержит запись.
- **AC-5 (Re-crawl Manual):** тестовый HTML с добавленной FAQPage-schema → re-crawl детектирует присутствие, Score пересчитан, delta > 0. Без использования CMS API.
- **AC-6 (No false alert):** Mock-данные: метрика упала, но внутри CI → алерт НЕ отправлен. Тест фиксирует.
- **AC-7 (Tenant алерт-настройки):** тенант с `alert_channels: [email]` → Telegram не вызывается (mock).

## Contracts touched

- **`verification` context:** `readiness_deltas` таблица, `visibility_trends` таблица, `evidence_snapshots` таблица; `POST /verify/readiness`, `GET /verify/visibility-trend`.
- **`notifications` context:** `notification_configs` (tenant_id, channel, threshold), `notification_log`; адаптеры email/Telegram/webhook. Стаб-контракт; конфигурации — JIT.
- Зависит от: `scoring` (P3), `metrics.visibility_metrics` (P5), `crawler` (P2/re-crawl).
- Раскрывает evidence-данные для Manual/Auto track retention; алерты — для удержания тенантов.

## Exit-gate

| Критерий | Порог |
|---|---|
| Readiness-delta корректна | AC-1 пройден |
| No false positives Visibility | AC-2 пройден |
| Evidence-скриншоты | AC-3 (файл сохранён) |
| Алерт при деградации | AC-4 (email + Telegram вызваны) |
| Re-crawl без API | AC-5 пройден |
| No false alert | AC-6 пройден |
| Аудит tier 3 | PASS (3 линзы: correctness · security · compliance) |

## Decomposition hints for planner

1. `backend-implementer` реализует `ReadinessDeltaService` (Score пересчёт + diff без краула).
2. `backend-implementer` реализует `VisibilityTrendService` (тренд + CI-сравнение → is_significant).
3. `crawler-probe-specialist` (Sonnet) реализует re-crawl для Manual track (FR-5.5): краул HTML + schema-детект.
4. `backend-implementer` реализует evidence-захват (Playwright скриншоты в Celery-задаче).
5. `backend-implementer` реализует `NotificationService` (email/Telegram/webhook адаптеры + tenant конфиг).
6. `tester` пишет тесты: no-false-positive (AC-2, AC-6), re-crawl без API (AC-5).
7. Аудит tier 3: correctness (no false wins) · security (скриншоты — ПД?) · compliance.
