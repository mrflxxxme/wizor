# Context: `autofix` — Auto-Fix Orchestration & Trust Ladder

**Purpose:** Оркеструет полный цикл авто-применения правок: управление trust-ladder (approval-gate по умолчанию → opt-in auto по типу правки), ведение append-only audit log всех изменений (что / где / когда / кем / diff), версионирование состояний, 1-click rollback, DPA-флоу (auto-fix недоступен до акцепта). Является «транзакционным координатором» между `recommendations`, `patches`, `connectors` в Auto track.

**Owns (data):** Очередь правок с approval-статусами, append-only audit log (неизменяем), версии состояний (для rollback), DPA-акцепты (с датой и версией соглашения), конфигурация trust-ladder по типам правок.

**Track:** auto

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P10]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** connectors

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 1** — Auto track — единственный, где возможна запись; DPA/API — gate только Auto track, не входа в продукт.
- **§6 инвариант 3** — Идемпотентность + обратимость: каждая правка должна быть применима повторно без побочных эффектов и откатываема 1-click; audit log append-only (запрет мутации строк).
- **§6 инвариант 10** — Видимый контент (FAQ) **никогда** не авто-применяется; пользователь должен явно подтвердить через review/merge-flow до публикации.
- DPA акцептован ДО первой авто-правки; факт акцепта хранится неизменно.
- Rollback тоже логируется в audit log.

**Phase refs:** P10 (auto track: trust-ladder + rollback + DPA-оркестрация, gated by P0 и P9).
