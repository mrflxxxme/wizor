# Context: `verification` — Verification & Evidence Capture

**Purpose:** Двухуровневая верификация эффекта применённых правок. Быстрый tier: Readiness-delta (немедленный пересчёт Score до/после, FR-5.1). Медленный tier: Visibility/Citation-delta по retrieval-поверхностям через повторные probe во времени (FR-5.2). Захватывает evidence: скриншоты/снапшоты ответов LLM до/после для кейсов и доверия (FR-5.3). Re-crawl верификация (FR-5.5): работает в Manual track — повторный краул публичных страниц подтверждает, что правка появилась в HTML без write-доступа.

**Owns (data):** Delta-записи (Score до/после + timestamp), evidence-снапшоты (скриншоты ответов с привязкой к промпту/модели/дате), алерт-конфигурации, история трендов верификации.

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P8]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** scoring, metrics

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 7** — «Реальный» Visibility-сдвиг заявляется только вне полосы шума (N≥5+CI); система не заявляет улучшение внутри шума (FR-5.2).
- Re-crawl верификация работает без write-доступа к сайту — доступна в Manual track (FR-5.5).
- Evidence-снапшоты хранятся с датой и привязкой к промпту/модели (не мутируются после записи).

**Phase refs:** P8 (верификация, re-crawl, evidence, алерты), P5 (алерты деградации через notifications).
