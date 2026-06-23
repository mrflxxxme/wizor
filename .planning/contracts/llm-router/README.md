# Context: `llm-router` — LLM Router & Provider Gateway

**Purpose:** Provider-agnostic абстракция для всех LLM-вызовов платформы. RU-default: GigaChat / YandexGPT для генерации контента (FAQ, рекомендации) — ПД клиента по умолчанию обрабатываются RU-моделями. OSS self-hosted fallback (Qwen 2.5 / Saiga via vLLM) для batch-cost оптимизации. Иностранные модели (OpenAI, Anthropic) — opt-in для незначительных/нечувствительных задач. Минимизирует vendor lock-in. Также маршрутизирует LLM-вызовы probe-контекста к нужному провайдеру/ноде с учётом dual-geo требований.

**Owns (data):** Конфигурации провайдеров, маршрутные правила (задача → провайдер/модель), статистика uncertainty (для каждого провайдера), rate-limit и retry-состояния.

**Track:** infra

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P4]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** —

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 6** — Контент клиента по умолчанию обрабатывается RU-моделями; иностранные — только opt-in.
- **§6 инвариант 4** (косвенно) — Роутер не направляет probe-запросы к ChatGPT/Perplexity через RU-IP; это ответственность probe-контекста, но роутер предоставляет правила маршрутизации.
- Секреты API-ключей провайдеров хранятся в Vault / Yandex Lockbox, не в коде (§6 инвариант 9).

**Phase refs:** P4 (LLM-router, infra), P5 (probe использует роутер), P6 (FAQ-gen через роутер).
