# Context: `iam` — Identity & Access Management

**Purpose:** Аутентификация пользователей (Keycloak/OIDC), управление мультиарендностью (`tenant_id` с дня 1), хранение entitlements дорожек доступа (Tier 0 / Manual / Auto). Производит `user_id` + токены; все downstream-контексты потребляют `user_id`, не обращаясь к таблицам `iam` напрямую. Публичный вход (Tier 0 Instant Audit) работает без аутентификации — контекст предоставляет публичный гейт без сессии.

**Owns (data):** Записи пользователей, сессии, refresh-токены, OAuth-линковки, consents (ПДн), DPA-акцепты дорожки Auto, entitlements тарифов.

**Track:** infra

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P1 / P9]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** —

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 8** — Multi-tenant изоляция: `tenant_id` обязателен в каждой записи, cross-tenant утечка недопустима.
- **§6 инвариант 1** — Read-only-граница: DPA/API требуются только для Auto track, не для входа в продукт; Tier 0 и Manual работают без write-доступа клиента.
- **§6 инвариант 6** — ПДн клиентов хостятся в РФ (Yandex Cloud); согласие по 152-ФЗ фиксируется до регистрации.
- **§6 инвариант 9** — Секреты (токены провайдеров, OAuth credentials) хранятся зашифрованными (Vault / Yandex Lockbox), не в коде.

**Phase refs:** P1 (multi-tenant foundation), P9 (auth + billing + onboarding).
