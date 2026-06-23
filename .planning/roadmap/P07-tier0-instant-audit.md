---
phase: P7
slug: tier0-instant-audit
title: "Tier 0 — Instant Audit (no-auth PLG)"
status: planned
tier: 3
track: read-only
depends_on: [P2, P3, P4, P5, P6]
gated_by: []
contracts: [iam, crawler, scoring, probe, metrics, recommendations, patches]
specialists: [geo-domain-expert, devops-infra-specialist]
prd_refs: [§4.1, §9.1, §9.4, §5]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): ⭐ Первая монетизируемая точка. PLG no-auth вход: пользователь вводит URL → получает AI-Readiness Score + competitive gap + copy-paste патчи + базовая Visibility (probe, 1 прогон). Без регистрации, без API. Rate-limited (per-IP). Упаковывает P2–P6 в единый публичный эндпоинт. Frontend: landing-страница + результат-страница. PostHog: воронка Tier0→регистрация. -->

## Goal

Запустить публичный «Instant Audit» — PLG-лид-магнит, первая монетизируемая точка продукта. Пользователь вводит URL без регистрации и получает полный read-only аудит. Цель: начать сбор кейсов и конверсионных данных Tier0→платный.

## In scope

- **Публичный эндпоинт `POST /api/public/audit`:** принимает `{url}` без auth-токена; запускает краул → Score → базовый probe (1 прогон × 4 модели, без полной N≥5 для скорости) → competitive gap → патчи.
- **Rate-limiting (per-IP):** жёсткий лимит (напр. 3 аудита/IP/день); превышение → 429 с graceful сообщением.
- **Результат-страница (frontend):** AI-Readiness Score с компонентами, competitive gap summary, copy-paste патчи (топ-3), базовый Visibility Score (1 прогон, с disclaimer о точности). CTA «Зарегистрируйтесь для полного мониторинга».
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

- **AC-1 (end-to-end):** `POST /api/public/audit {"url": "https://example.com"}` без токена → HTTP 200 + JSON с `score`, `components[]`, `competitors_gap`, `patches[]`, `visibility_preview`. Время ответа < 90 сек.
- **AC-2 (rate-limit):** 4-й запрос с одного IP в тот же день → HTTP 429 с `retry_after`.
- **AC-3 (read-only инвариант):** аудит Tier-0 не производит ни одного PUT/POST/DELETE на клиентский сайт (тест логов).
- **AC-4 (disclaimer):** поле `visibility_preview.disclaimer` непустое в ответе; в UI disclaimer виден.
- **AC-5 (PostHog):** после реального Tier-0 аудита в PostHog UI видны события `tier0_audit_started` и `tier0_audit_completed` с `distinct_id=<anon_id>`.
- **AC-6 (изоляция anon):** `SELECT * FROM crawl_results WHERE tenant_id != 'TIER0_ANON'` — Tier-0 данные не смешиваются с платными тенантами.
- **AC-7 (патч валиден):** все JSON-LD патчи в Tier-0 ответе проходят schema-валидатор (FR-1.2).
- **AC-8 (TTL чистка):** Tier-0 результаты старше 7 дней удаляются (Celery-задача `clean_tier0_results` работает).

## Contracts touched

- **`iam` (public):** `TIER0_ANON` системный tenant; публичный эндпоинт без JWT.
- Упаковывает: `crawler`, `scoring`, `probe`, `metrics`, `recommendations`, `patches` — все через единый `AuditOrchestrator`.
- PostHog события добавляются к `iam`/frontend контрактам.

## Exit-gate

| Критерий | Порог |
|---|---|
| End-to-end Tier-0 без auth | AC-1 (< 90 сек) |
| Rate-limit | AC-2 (429 на 4-й запрос) |
| Read-only инвариант | AC-3 пройден |
| Disclaimer | AC-4 присутствует |
| PostHog воронка | AC-5 (события видны) |
| Anon изоляция | AC-6 пройден |
| Patch валидность | AC-7 пройден |
| TTL чистка | AC-8 пройден |
| Аудит tier 3 | PASS (3 линзы: correctness · security · compliance) |

## Decomposition hints for planner

1. `backend-implementer` реализует `AuditOrchestrator` — последовательно вызывает crawl → score → probe (1 run) → gap → patches.
2. `backend-implementer` создаёт публичный роут `/api/public/audit` с IP rate-limiter (Redis sliding window).
3. `frontend-implementer` создаёт landing-страницу (URL-инпут) + результат-страницу (SSR).
4. `backend-implementer` реализует Celery-задачу TTL-чистки `clean_tier0_results`.
5. `devops-infra-specialist` настраивает rate-limit на уровне инфры (nginx/Cloudflare).
6. PostHog события инструментируются в backend (completion) и frontend (CTA-клик).
7. `geo-domain-expert` ревьюит UI результат-страницы: понятность Score, наличие disclaimer, CTA.
8. Аудит tier 3: correctness · security (rate-limit bypass) · compliance (152-ФЗ для anon-данных).
