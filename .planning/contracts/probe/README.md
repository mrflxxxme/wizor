# Context: `probe` — LLM Probe Monitoring

**Purpose:** Запускает LLM-пробы по целевым промптам пользователя через 4 модели (ChatGPT, Perplexity, Алиса/Нейро, GigaChat) в dual-geo конфигурации. RU-модели — через Yandex Cloud Foundation Models / GigaChat API с RU-нод; ChatGPT/Perplexity — через зарубежные ноды (Hetzner/Selectel) + резидентные прокси. Каждый промпт прогоняется N ≥ 5 раз на модель; результаты хранятся как распределения для вычисления доверительных интервалов. Выполняется async batch через Celery + Redis.

**Owns (data):** Результаты прогонов (сырые ответы LLM + метаданные: модель, гео-нода, timestamp, попытка), агрегированные распределения, конфигурации промптов.

**Track:** read-only

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P5]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** llm-router

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 4** — Ни один probe к ChatGPT / Perplexity **не выполняется с РФ-IP**. Маршрутизация через зарубежные ноды и резидентные прокси обязательна; нарушение = блокирующий аудит-дефект.
- Каждый промпт прогоняется N ≥ 5 раз; хранится полное распределение, не только агрегат.
- Сбой отдельной попытки не «роняет» весь батч — изоляция на уровне job.

**Phase refs:** P5 (probe-мониторинг), P7 (базовая Visibility в Tier 0 Instant Audit).
