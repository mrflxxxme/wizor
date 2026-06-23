# Context: `recommendations` — Recommendations & Competitive Gap

**Purpose:** Генерирует приоритизированный лист фиксов с прогнозом impact и пометкой «авто-применимо / требует review». Выполняет competitive gap analysis: краулит конкурентов, которых цитируют LLM по целевым промптам, сравнивает их Readiness/структуру с сайтом клиента, формирует доказательную базу. Генерирует FAQ-черновики (answer-first, 50–150 слов) через llm-router. Формирует honest forecast: Readiness-проекция (детерминированно) + Visibility-прогноз только как диапазон с доверием/бенчмарками.

**Owns (data):** Листы рекомендаций (версионированные), competitive gap-отчёты, FAQ-черновики (статус draft/approved), прогнозы impact.

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P6]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** scoring, metrics

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 2** — Honest forecast: UI нигде не показывает гарантированный Visibility-%; все вероятностные прогнозы помечены и сопровождаются доверительным диапазоном; Readiness-проекция детерминирована.
- FAQ-черновики помечены как `draft`; контекст не публикует их без review — это задача `autofix` / `connectors` после явного confirm.
- Competitive gap показывает конкретные структурные отличия (schema-типы, FAQ, answer-first) без выдуманных процентов.

**Phase refs:** P6 (рекомендации + competitive gap + honest forecast), P7 (в составе Tier 0 Instant Audit).
