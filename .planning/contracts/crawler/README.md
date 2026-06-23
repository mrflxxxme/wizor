# Context: `crawler` — Site Crawler & Auditor

**Purpose:** Read-only краулинг сайта клиента и сайтов конкурентов (тех, кого цитируют LLM по целевым промптам). Извлекает структуру HTML (h1–h3, семантические теги), JSON-LD разметку, robots.txt, sitemap, HTTP-коды, Core Web Vitals, FAQ-блоки, признаки клиентского рендеринга (SPA). Также выполняет re-crawl для верификации применённых патчей без API (FR-5.5, Manual track). Реализован на Crawlee (Python) + Playwright для SPA.

**Owns (data):** Снапшоты страниц, извлечённые структурные сигналы, история краулов (для delta/re-crawl), crawl-задания и статусы.

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P2]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** —

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- Краулер выполняет только **read-only** операции; запись на сайт клиента исключена на уровне этого контекста.
- Повторный краул (re-crawl) проверяет факт наличия правки в публичном HTML без write-доступа — основа Manual track верификации.

**Phase refs:** P2 (crawler/audit), P6 (competitive gap — краул конкурентов), P8 (re-crawl verification).
