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
<!-- HEAD-SUMMARY (≤500т): Инфра-фаза уровня 4. Закрывает петлю монетизации: Keycloak полная JWT-auth, multi-tenant полная изоляция, ЮKassa биллинг (физ+юр лица), 3 тарифа (Starter/Pro/Business) × режимы Manual/Auto, full-feature trial (дефолты ADR-0023: 14 дн self-serve / 30 дн design-партнёры; цена Manual = Auto), self-serve онбординг с time-to-first-verified-fix < 24ч + редактор промптов (ADR-0024), entitlements-система (breadth-gate по тарифу). 5-линзовый аудит (tier 4). После P9 продукт готов к первым платящим пользователям.

Дефолты, ранее блокировавшие фазу (trial/pricing/trust-ladder), зафиксированы в ADR-0023 с маркером revisit_after. Каждый AC помечен классом (ADR-0022). -->

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
  - Каждый тариф в двух режимах: **Manual** (без API, копипаст) и **Auto** (API+DPA, авто-применение). **Цена Manual = Auto** внутри тарифа (ADR-0023): Auto — ценность внутри тарифа, гейт Auto = только акцепт DPA, не деньги.
- **Entitlements-система:** `entitlements` таблица (tenant_id, plan, mode, features[]); все API читают entitlements → breadth-gate по тарифу.
- **Trial (NFR-8, дефолт ADR-0023):** full-feature, time-limited — **14 дн self-serve; 30 дн design-партнёры**; real аудит + первый фикс → Readiness-delta как конверсионный хук; trial → paid без потери данных (FR-6.3 AC).
- **Self-serve онбординг (FR-6.1):** подключение сайта → аудит → **редактор промптов (ADR-0024:** показ авто-сгенерированных промптов из crawl, правка/добавление/удаление, лимит числа по тарифу, каждая правка → новая `prompt_set_version`) → первая правка (aha); `time-to-first-verified-fix` < 24 ч для типового WP-сайта без участия поддержки.
- **Trust-ladder дефолт (ADR-0023, применяется в P10):** approval-gate на всё по умолчанию; per-type opt-in auto-apply машиночитаемого слоя доступен пользователю сразу (без порога «после N успешных»); видимый контент (FAQ) — никогда не auto. В P9 фиксируется как entitlement/настройка тенанта.
- **Frontend (ADR-0026, UI-SPEC):** `login`/`register` (Keycloak OIDC), `onboarding` wizard (4 шага + prompt-editor), `billing` (3 тарифа × Manual/Auto, trial-статус, история платежей), `prompts` (редактор prompt-set с лимитом по тарифу).
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

- **AC-1 (онбординг time-to-fix) [live-only]:** happy-path тест на тестовом WP-сайте с WP-коннектором (Auto режим): регистрация → аудит → probe → первый фикс применён → Readiness-delta показана; общее время ≤ 24 ч (automated e2e). Blocked до test-WP + funded-ключей + прода (P6.5).
- **AC-2 (tenant изоляция full) [mock-verifiable]:** пользователь тенанта A не может получить данные тенанта B через любой авторизованный API-запрос (pentest-like тест: swap JWT claim → 403).
- **AC-3 (ЮKassa webhook) [mock-verifiable]:** mock ЮKassa webhook `payment.succeeded` → подписка тенанта переходит в `active`; `payment.cancelled` → `suspended`. Live-подтверждение — AC-10.
- **AC-4 (breadth-gate) [mock-verifiable]:** Starter-тенант пытается добавить 2-й сайт → 403 с кодом `plan_limit_exceeded`.
- **AC-5 (trial → paid) [mock-verifiable]:** тенант на trial применил 2 фикса; конвертация в paid → `trial_fixes` сохранены, данные не потеряны. Trial-длительность = 14 дн self-serve / 30 дн партнёры (ADR-0023, конфиг-тест).
- **AC-6 (Manual vs Auto) [mock-verifiable]:** Manual-тенант пытается вызвать `POST /apply-fix` (авто-применение) → 403 `mode_not_allowed`; Auto-тенант — 200. Цена тарифа одинакова для обоих режимов (ADR-0023, тест entitlements).
- **AC-7 (PostHog) [live-only]:** события воронки фиксируются в PostHog UI с корректным `tenant_id`. Blocked до PostHog-инстанса (P6.5).
- **AC-8 (prompt-editor, ADR-0024) [mock-verifiable]:** онбординг показывает авто-сгенерированные промпты; правка/добавление создаёт новую `prompt_set_version`; число промптов ограничено тарифом (Starter<Pro<Business, тест лимита).
- **AC-9 (frontend auth/onboarding/billing, ADR-0026) [mock-verifiable]:** login/register (OIDC-редирект), onboarding wizard (4 шага + prompt-editor), billing (тарифы × режимы, trial-статус) рендерятся и проходят happy-path против mock-API (vitest/RTL/Playwright-компонент).
- **AC-10 (live ЮKassa sandbox) [live-only]:** реальный ЮKassa sandbox webhook `payment.succeeded` → подписка `active`. Blocked до ЮKassa sandbox-ключей (PLACEHOLDERS).

## Contracts touched

- **`iam` context** (полный): Keycloak realm конфигурация; `users`, `tenants`, `entitlements` таблицы; JWT middleware. `api.yaml` — JIT при планировании фазы.
- **`billing` context:** `subscriptions` (tenant_id, plan, mode, status, trial_ends_at, paid_until); ЮKassa webhooks; `POST /billing/subscribe`, `GET /billing/status`. Стаб → JIT.
- Взаимодействует с: всеми read-only контрактами (breadth-gate) + `autofix` context (mode-gate для Auto track).

## Exit-gate

| Критерий | Порог |
|---|---|
| Tenant изоляция | AC-2 (403 при swap JWT) [mock] |
| ЮKassa webhooks | AC-3 (active/suspended, mock) [mock] |
| Breadth-gate | AC-4 (403 Starter 2-й сайт) [mock] |
| Trial → paid без потери данных | AC-5 (14/30 дн ADR-0023) [mock] |
| Manual vs Auto gate + pricing-паритет | AC-6 (mode-gate; цена Manual=Auto) [mock] |
| Prompt-editor | AC-8 (версионирование + лимит тарифа) [mock] |
| Frontend auth/onboarding/billing | AC-9 пройден [mock] |
| Онбординг time-to-fix | AC-1 (< 24 ч e2e) [live-only, blocked: test-WP+funded+P6.5] |
| PostHog воронка | AC-7 (события в UI) [live-only, blocked: PostHog/P6.5] |
| ЮKassa sandbox live | AC-10 [live-only, blocked: ЮKassa sandbox-ключи] |
| Аудит tier 4 | PASS (5 линз: correctness · security · compliance · tests · architecture) |

**Live-only AC блокированы до founder-ресурса** (ADR-0022): AC-1 (test-WP+funded+прод), AC-7 (PostHog), AC-10 (ЮKassa sandbox). Mock-verifiable подмножество мёржится раньше; гейт не закрывается без live-only части.

## Decomposition hints for planner

1. `backend-implementer` настраивает Keycloak realm, client, роли; JWT middleware для FastAPI.
2. `backend-implementer` реализует Alembic-миграции `subscriptions`, `entitlements`.
3. `backend-implementer` интегрирует ЮKassa SDK: создание подписки, webhook-обработчик.
4. `backend-implementer` реализует entitlements middleware (breadth-gate, mode-gate).
5. `frontend-implementer` создаёт регистрацию/логин (Keycloak OIDC), onboarding wizard (4 шага), billing-страницу.
6. `compliance-152fz-specialist` (Opus) ревьюит: хранение платёжных данных (ЮKassa — не ПД, но чек), DPA для Auto-mode, политика обработки ПД.
7. `tester` пишет e2e: happy-path онбординг, tenant isolation pentest, trial→paid.
8. Полный 5-линзовый аудит (tier 4) — особый фокус security + compliance (биллинг, ПД).
