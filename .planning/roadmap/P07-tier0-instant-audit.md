---
phase: P7
slug: tier0-instant-audit
title: "Tier 0 — Instant Audit (no-auth PLG)"
status: planned
tier: 3
track: read-only
depends_on: [P2, P3, P4, P5, P6, P6.5]
gated_by: []
contracts: [iam, crawler, scoring, probe, metrics, recommendations, patches]
specialists: [geo-domain-expert, devops-infra-specialist, frontend-implementer]
prd_refs: [§4.1, §9.1, §9.4, §5]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): ⭐ Первая монетизируемая точка. PLG no-auth вход: пользователь вводит URL → получает AI-Readiness Score + competitive gap + copy-paste патчи + базовая Visibility (probe, 1 прогон). Без регистрации, без API. **Асинхронная job-модель (ADR-0025):** POST возвращает job_id мгновенно, результат-страница наполняется поэтапно (Score+патчи ≤90с, visibility+gap ≤5мин). Rate-limited (per-IP). Упаковывает P2–P6 в единый публичный эндпоинт. Требует прод (P6.5). Frontend: landing + async-результат. PostHog: воронка Tier0→регистрация.

Каждый AC помечен классом (ADR-0022): [mock-verifiable] обязателен до PR; [live-only] blocked_pending_resource. -->

## Goal

Запустить публичный «Instant Audit» — PLG-лид-магнит, первая монетизируемая точка продукта. Пользователь вводит URL без регистрации и получает полный read-only аудит. Цель: начать сбор кейсов и конверсионных данных Tier0→платный.

## In scope

- **Публичный async-эндпоинт (ADR-0025) `POST /api/public/audit`:** принимает `{url}` без auth-токена; валидирует URL, ставит job в Celery, **мгновенно** возвращает `{job_id, status: queued}`. Обработка: prompt-set авто-ген (ADR-0024) → краул → Score → базовый probe (1 прогон × 4 модели, без полной N≥5 для скорости) → competitive gap → патчи. `GET /api/public/audit/{job_id}` отдаёт частичный результат по мере готовности со стадиями (`stages: {score, visibility, gap}`).
- **Два порога наполнения (ADR-0025):** Порог 1 (≤90с) — `score`, `components[]`, `patches[]` (быстрый детерминированный слой). Порог 2 (≤5мин) — `visibility_preview` (probe), `competitors_gap` (probe + краул конкурентов).
- **Rate-limiting (per-IP):** жёсткий лимит (напр. 3 аудита/IP/день) на `POST` (постановка job), не на polling; превышение → 429 с graceful сообщением.
- **Результат-страница (frontend, ADR-0026, UI-SPEC):** async прогресс-страница `/audit/[jobId]` — поллит job, наполняется поэтапно, показывает стадии/плейсхолдеры; затем AI-Readiness Score с компонентами, competitive gap summary, copy-paste патчи (топ-3), базовый Visibility Score (1 прогон, с disclaimer о точности). CTA «Зарегистрируйтесь для полного мониторинга».
- **Анонимный tenant:** каждый Tier-0 аудит исполняется под системным `tenant_id=TIER0_ANON` с изоляцией данных; результаты хранятся 7 дней (GDPR/152-ФЗ-лёгкий режим).
- **PostHog воронка:** события `tier0_audit_started`, `tier0_audit_completed`, `tier0_cta_clicked` → North Star funnel.
- **Frontend landing + result:** Next.js страница с URL-инпутом; результат-страница (SSR/ISR); shadcn/ui компоненты.
- **Rate-limit и abuse-protection:** Cloudflare/Yandex Shield или nginx rate-limit; `robots.txt` для Tier-0 эндпоинта — нет индексирования.
- **Probe в Tier-0 режиме:** 1 прогон (не N≥5), с явным UI-disclaimer «предварительная оценка, для точных данных — полный мониторинг».

## Out of scope

- Регистрация, auth, биллинг (→ P9).
- Полная N≥5 probe (только 1 прогон в Tier-0 для скорости).
- Регулярный мониторинг (→ P9 Manual/Auto track).
- Re-crawl верификация (→ P8).
- FAQ-генерация (только патчи машиночитаемого слоя в Tier-0).
- White-label, агентский доступ (→ фаза B).

## Functional requirements

- **FR-P7-1** (из §4.1 + §9.1): URL → полный аудит без auth; результат содержит Score + competitive gap + ≥3 copy-paste патча + базовый Visibility (1 прогон). Всё read-only.
- **FR-P7-2** (из §9.1): rate-limit per-IP; превышение → 429 с сообщением.
- **FR-P7-3** (из §9.4/§5 North Star): PostHog воронка tier0_audit_started → tier0_audit_completed → tier0_cta_clicked активна с первого дня.
- **FR-P7-4** (из §4.1): probe в Tier-0 отмечен UI-disclaimer об ограниченной точности (1 прогон, не N≥5).

## Acceptance criteria

- **AC-1 (async, порог 1) [mock-verifiable]:** `POST /api/public/audit {"url": "..."}` без токена → HTTP 202 + `{job_id, status: queued}` мгновенно (< 2 сек). `GET /api/public/audit/{job_id}` в пределах **≤90 сек** отдаёт `score`, `components[]`, `patches[]` (с фиксированными mock-сервисами в тесте — детерминированно).
- **AC-1b (async, порог 2) [mock-verifiable]:** тот же `GET job` в пределах **≤5 мин** дополняется `visibility_preview` и `competitors_gap`; до готовности поля отсутствуют/помечены `pending`, стадии видны в `stages`.
- **AC-2 (rate-limit) [mock-verifiable]:** 4-й `POST` с одного IP в тот же день → HTTP 429 с `retry_after`; polling `GET` не лимитируется.
- **AC-3 (read-only инвариант) [mock-verifiable]:** аудит Tier-0 не производит ни одного PUT/POST/DELETE на клиентский сайт (тест логов + структурный read-only guard P2).
- **AC-4 (disclaimer) [mock-verifiable]:** поле `visibility_preview.disclaimer` непустое; в UI disclaimer виден (frontend-тест); нет гарантированного Visibility-% (инвариант §6.2).
- **AC-5 (PostHog) [live-only]:** после реального Tier-0 аудита в PostHog UI видны события `tier0_audit_started` и `tier0_audit_completed` с `distinct_id=<anon_id>`. Blocked до PostHog-инстанса (P6.5).
- **AC-6 (изоляция anon) [mock-verifiable]:** `SELECT * FROM crawl_results WHERE tenant_id != 'TIER0_ANON'` — Tier-0 данные не смешиваются с платными тенантами (integration-тест).
- **AC-7 (патч валиден) [mock-verifiable]:** все JSON-LD патчи в Tier-0 ответе проходят schema-валидатор (FR-1.2).
- **AC-8 (TTL чистка) [mock-verifiable]:** Tier-0 результаты старше 7 дней удаляются (Celery-задача `clean_tier0_results` работает; integration-тест с состаренными записями).
- **AC-9 (frontend async, ADR-0026) [mock-verifiable]:** страница `/audit/[jobId]` поллит job, рендерит стадии/плейсхолдеры и поэтапное наполнение против mock-job (vitest/RTL); landing с URL-инпутом валидирует и создаёт job.
- **AC-10 (live Tier-0 end-to-end) [live-only]:** на реальном URL полный async-путь отрабатывает: порог 1 ≤90с, порог 2 ≤5мин, результат осмысленный. Blocked до funded LLM-ключей + egress-ноды + прода (P6.5).

## Contracts touched

- **`iam` (public):** `TIER0_ANON` системный tenant; публичный эндпоинт без JWT.
- Упаковывает: `crawler`, `scoring`, `probe`, `metrics`, `recommendations`, `patches` — все через единый `AuditOrchestrator`.
- PostHog события добавляются к `iam`/frontend контрактам.

## Exit-gate

| Критерий | Порог | Класс |
|---|---|---|
| Async порог 1 (Score+патчи) | AC-1 (≤90с в GET job) | mock |
| Async порог 2 (visibility+gap) | AC-1b (≤5мин) | mock |
| Rate-limit | AC-2 (429 на 4-й POST) | mock |
| Read-only инвариант | AC-3 пройден | mock |
| Disclaimer + honest-forecast | AC-4 присутствует | mock |
| Anon изоляция | AC-6 пройден | mock |
| Patch валидность | AC-7 пройден | mock |
| TTL чистка | AC-8 пройден | mock |
| Frontend async-страница | AC-9 пройден | mock |
| PostHog воронка | AC-5 (события в UI) | **live-only** (blocked: PostHog-инстанс/P6.5) |
| Live Tier-0 end-to-end | AC-10 | **live-only** (blocked: funded LLM + egress + P6.5) |
| Аудит tier 3 | PASS (3 линзы: correctness · security · compliance) | — |

**Live-only AC блокированы до founder-ресурса** (ADR-0022): AC-5 (PostHog-инстанс), AC-10 (funded LLM + egress + прод P6.5). Mock-verifiable подмножество мёржится раньше; гейт не закрывается без live-only части.

## Decomposition hints for planner

1. `backend-implementer` реализует `AuditOrchestrator` — последовательно вызывает crawl → score → probe (1 run) → gap → patches.
2. `backend-implementer` создаёт публичный роут `/api/public/audit` с IP rate-limiter (Redis sliding window).
3. `frontend-implementer` создаёт landing-страницу (URL-инпут) + результат-страницу (SSR).
4. `backend-implementer` реализует Celery-задачу TTL-чистки `clean_tier0_results`.
5. `devops-infra-specialist` настраивает rate-limit на уровне инфры (nginx/Cloudflare).
6. PostHog события инструментируются в backend (completion) и frontend (CTA-клик).
7. `geo-domain-expert` ревьюит UI результат-страницы: понятность Score, наличие disclaimer, CTA.
8. Аудит tier 3: correctness · security (rate-limit bypass) · compliance (152-ФЗ для anon-данных).
