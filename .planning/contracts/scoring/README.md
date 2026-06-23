# Context: `scoring` — AI-Readiness Score

**Purpose:** Вычисляет детерминированный AI-Readiness Score на основе структурных сигналов сайта (Discovery + Comprehension layer). Score воспроизводим: одинаковый вход → одинаковый выход. Раскрывает веса компонентов пользователю. Также используется для Readiness-delta (быстрый tier проверки, FR-5.1): немедленный пересчёт Score до/после применения правки.

**Owns (data):** Расчёты Score по ревизиям снапшотов, веса факторов, история Score по сайту (для delta-трекинга).

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P3]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** crawler

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 5** — `llms.txt` **не входит** в citation-вес Score; не позиционируется как citation-драйвер. Score отражает только реальные citation-рычаги (schema, FAQ, answer-first).
- Score детерминирован и версионирован: смена формулы весов — новая версия Score, не мутация истории.

**Phase refs:** P3 (AI-Readiness Score), P6 (Readiness-проекция для рекомендаций), P8 (Readiness-delta верификация).
