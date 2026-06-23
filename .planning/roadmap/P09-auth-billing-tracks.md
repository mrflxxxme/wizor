---
phase: P9
slug: auth-billing-tracks
title: "Auth + биллинг + онбординг + дорожки Manual/Auto"
status: planned
tier: 4
track: infra
depends_on: [P7, P8]
gated_by: []
contracts: [iam, billing]
specialists: [compliance-152fz-specialist, devops-infra-specialist]
prd_refs: [EPIC-6/FR-6.1, EPIC-6/FR-6.2, EPIC-6/FR-6.3, §9.4, §4.1, §9.3/NFR-8]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Инфра-фаза уровня 4. Закрывает петлю монетизации: Keycloak полная JWT-auth, multi-tenant полная изоляция, ЮKassa биллинг (физ+юр лица), 3 тарифа (Starter/Pro/Business) × режимы Manual/Auto, full-feature trial ≥14–30 дн, self-serve онбординг с time-to-first-verified-fix < 24ч, entitlements-система (breadth-gate по тарифу). 5-линзовый аудит (tier 4). После P9 продукт готов к первым платящим пользователям. -->

## Goal

Запустить полный платный продукт: регистрация через Keycloak, ЮKassa биллинг, выбор тарифа и режима доступа (Manual/Auto), trial → платный конвертация без потери данных. Self-serve онбординг с достижением first-verified-fix < 24 часов.

## In scope

- **Keycloak полная JWT-auth (FR-6.2):** регистрация/логин (email+пароль, OAuth2), JWT-токены, refresh, OIDC; middleware для всех эндпоинтов; роли `owner`, `viewer` (agency-роли → фаза B).
- **Multi-tenant полная изоляция (FR-6.2):** tenant_id в JWT claims; все API-запросы фильтруются по tenant; `agency_mode` флаг (stub, активен в фазе B) не требует архитектурной миграции.
- **ЮKassa биллинг (FR-6.3):** оплата физ. и юр. лицами; recurring (подписка); webhooks подтверждения; хранение статуса подписки; auto-cancel при неоплате.
- **3 тарифа × режимы (§9.4):**
  - Starter (5 990 ₽): 1 сайт, WP-коннектор, monthly probe, машиночитаемый авто.
  - Pro (14 990 ₽): несколько сайтов, weekly probe, + FAQ-draft/review.
  - Business (29 990 ₽): больше сайтов, daily probe, расширенные правки.
  - Каждый тариф в двух режимах: **Manual** (без API, копипаст) и **Auto** (API+DPA, авто-применение).
- **Entitlements-система:** `entitlements` таблица (tenant_id, plan, mode, features[]); все API читают entitlements → breadth-gate по тарифу.
- **Trial (NFR-8):** full-feature, time-limited (≥14 дн self-serve; design-партнёры — 30 дн); real аудит + первый фикс → Readiness-delta как конверсионный хук; trial → paid без потери данных (FR-6.3 AC).
- **Self-serve онбординг (FR-6.1):** подключение сайта → аудит → предложенные промпты → первая правка (aha); `time-to-first-verified-fix` < 24 ч для типового WP-сайта без участия поддержки.
- **PLG-воронка:** PostHog события `user_registered`, `trial_started`, `first_fix_applied`, `converted_to_paid`.

## Out of scope

- Agency multi-tenant UX (N клиентских сайтов под одним агентством), agency-billing → фаза B.
- White-label кабинет → фаза B.
- Stripe (для экспортных пользователей) → фаза B.
- Keycloak SSO/корп-IdP → фаза C.
- On-premise деплой → фаза C.

## Functional requirements

- **FR-6.1** Self-serve онбординг: подключение сайта → аудит → предложенные промпты → первая правка.
  - **AC PRD:** `time-to-first-verified-fix` для типового WP-сайта < 24 ч; happy-path без участия поддержки.
- **FR-6.2** Keycloak/OIDC, multi-tenant-ready (tenant_id с дня 1).
  - **AC PRD:** схема данных изолирует тенантов; переход в agency-режим (фаза B) не требует миграции архитектуры.
- **FR-6.3** ЮKassa (физ + юр лица), 3 тарифа, full-feature trial.
  - **AC PRD:** тарифы гейтят breadth; trial конвертируется без потери данных.

## Acceptance criteria

- **AC-1 (онбординг time-to-fix):** happy-path тест на тестовом WP-сайте с WP-коннектором (Auto режим): регистрация → аудит → probe → первый фикс применён → Readiness-delta показана; общее время ≤ 24 ч (automated e2e).
- **AC-2 (tenant изоляция full):** пользователь тенанта A не может получить данные тенанта B через любой авторизованный API-запрос (pentest-like тест: swap JWT claim → 403).
- **AC-3 (ЮKassa webhook):** mock ЮKassa webhook `payment.succeeded` → подписка тенанта переходит в `active`; `payment.cancelled` → `suspended`.
- **AC-4 (breadth-gate):** Starter-тенант пытается добавить 2-й сайт → 403 с кодом `plan_limit_exceeded`.
- **AC-5 (trial → paid):** тенант на trial применил 2 фикса; конвертация в paid → `trial_fixes` сохранены, данные не потеряны.
- **AC-6 (Manual vs Auto):** Manual-тенант пытается вызвать `POST /apply-fix` (авто-применение) → 403 `mode_not_allowed`; Auto-тенант — 200.
- **AC-7 (PostHog):** события воронки фиксируются в PostHog UI с корректным `tenant_id`.

## Contracts touched

- **`iam` context** (полный): Keycloak realm конфигурация; `users`, `tenants`, `entitlements` таблицы; JWT middleware. `api.yaml` — JIT при планировании фазы.
- **`billing` context:** `subscriptions` (tenant_id, plan, mode, status, trial_ends_at, paid_until); ЮKassa webhooks; `POST /billing/subscribe`, `GET /billing/status`. Стаб → JIT.
- Взаимодействует с: всеми read-only контрактами (breadth-gate) + `autofix` context (mode-gate для Auto track).

## Exit-gate

| Критерий | Порог |
|---|---|
| Онбординг time-to-fix | < 24 ч (e2e тест) |
| Tenant изоляция | AC-2 (403 при swap JWT) |
| ЮKassa webhooks | AC-3 (active/suspended) |
| Breadth-gate | AC-4 (403 Starter 2-й сайт) |
| Trial → paid без потери данных | AC-5 пройден |
| Manual vs Auto gate | AC-6 пройден |
| PostHog воронка | AC-7 пройден |
| Аудит tier 4 | PASS (5 линз: correctness · security · compliance · tests · architecture) |

## Decomposition hints for planner

1. `backend-implementer` настраивает Keycloak realm, client, роли; JWT middleware для FastAPI.
2. `backend-implementer` реализует Alembic-миграции `subscriptions`, `entitlements`.
3. `backend-implementer` интегрирует ЮKassa SDK: создание подписки, webhook-обработчик.
4. `backend-implementer` реализует entitlements middleware (breadth-gate, mode-gate).
5. `frontend-implementer` создаёт регистрацию/логин (Keycloak OIDC), onboarding wizard (4 шага), billing-страницу.
6. `compliance-152fz-specialist` (Opus) ревьюит: хранение платёжных данных (ЮKassa — не ПД, но чек), DPA для Auto-mode, политика обработки ПД.
7. `tester` пишет e2e: happy-path онбординг, tenant isolation pentest, trial→paid.
8. Полный 5-линзовый аудит (tier 4) — особый фокус security + compliance (биллинг, ПД).
