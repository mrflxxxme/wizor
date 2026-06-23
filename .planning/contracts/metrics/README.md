# Context: `metrics` — Visibility & Citation Metrics

**Purpose:** Агрегирует сырые результаты probe-прогонов в продуктовые метрики с uncertainty-aware подходом: Visibility Score (композит), Coverage/Presence, Share of Voice (SoV), Citation Rate (явное цитирование/ссылка, отдельно от упоминания), Stability. Вычисляет полосу шума (доверительный интервал по N≥5 прогонам); «реальное» изменение = выход за полосу. UI показывает Score + 4 компонента с полосой шума; сырые распределения доступны по запросу.

**Owns (data):** Агрегированные метрики по сайту/промпту/модели/периоду, доверительные интервалы, история трендов.

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P5]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** probe

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 7** — Улучшение Visibility заявляется только вне полосы шума (N≥5+CI); система не декларирует улучшение внутри шума.
- **§6 инвариант 2** — Нигде нет гарантированного Visibility-%; всегда диапазон + доверие + бенчмарки.
- Sentiment-трекинг — вне scope MVP (фаза B).

**Phase refs:** P5 (Visibility-метрики), P6 (данные для рекомендаций / honest forecast), P8 (Visibility/Citation-delta верификация).
