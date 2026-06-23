# Context: `patches` — Patch Artifact Generator

**Purpose:** Генерирует готовые copy-paste артефакты для Manual track: JSON-LD сниппеты (Organization, FAQPage, Article и др.), строки robots.txt (разрешения AI-ботам), контент llms.txt / llms-full.txt, FAQ-блоки HTML. Каждый артефакт сопровождается инструкцией «куда вставить». Артефакты валидируются (rdflib + custom JSON-LD validator) до выдачи. Работает полностью без write-доступа к сайту — основа Manual track (FR-4.7, FR-3.4).

**Owns (data):** Версионированные патч-артефакты по рекомендациям, статус (generated / applied / superseded), привязка к рекомендации и снапшоту сайта.

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P6]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** recommendations

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- Артефакты доступны без подключения API/коннектора — это основной инструмент Manual track.
- Невалидный JSON-LD **не выдаётся** (pre-validation обязателен); пользователь видит причину.
- `llms.txt` генерируется как agent-infra артефакт, но **не позиционируется** как citation-драйвер (§6 инвариант 5).

**Phase refs:** P6 (генерация патчей), P7 (copy-paste патчи в Tier 0 Instant Audit).
