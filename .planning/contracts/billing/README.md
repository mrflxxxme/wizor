# Context: `billing` — Billing & Entitlements

**Purpose:** Управление тарифами (Starter / Pro / Business), trial-периодами, платёжными транзакциями через ЮKassa (физ. и юр. лица), entitlements дорожек (Manual / Auto track) и breadth-гейтингом (количество сайтов, частота probe, глубина правок). Конвертация trial в платный план без потери данных. Multi-tenant ready: изоляция биллинга по `tenant_id`. Будущее: Stripe для экспорта (фаза B).

**Owns (data):** Подписки и их статусы, платёжные транзакции, trial-метаданные, entitlements по тарифу и дорожке, история платежей.

**Track:** infra

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P9]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** iam

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 8** — Биллинговые данные изолированы по `tenant_id`; cross-tenant утечка недопустима.
- **§6 инвариант 6** — Обработка платёжных ПД клиентов — в РФ (ЮKassa, Yandex Cloud); 152-ФЗ комплаенс обязателен.
- Trial конвертируется без потери данных и без потери истории аудитов/патчей.
- Entitlement Auto track включается только совместно с DPA-акцептом (из `autofix`/`iam`).

**Phase refs:** P9 (биллинг + онбординг + тарифы).
