---
phase: P4
slug: llm-router
title: "LLM-router (provider-agnostic, RU-default)"
status: planned
tier: 4
track: infra
depends_on: [P1]
gated_by: []
contracts: [llm-router]
specialists: [llm-router-specialist]
prd_refs: [§9.3/NFR-3, §12, §3/принцип_6]
model_default: opus
---
<!-- HEAD-SUMMARY (≤500т): Инфра-фаза уровня 4. Provider-agnostic LLM-gateway: RU-default (GigaChat/YandexGPT), OSS self-hosted (vLLM + Qwen/Saiga) для batch-cost, иностранные (OpenAI/Anthropic) — opt-in. Минимальный LangChain/LlamaIndex. Единый интерфейс для FAQ-генерации (P6) и probe-мониторинга (P5). 5-линзовый аудит (tier 4). -->

## Goal

Создать provider-agnostic LLM-роутер, который изолирует продукт от vendor lock-in, обеспечивает RU-default (152-ФЗ), экономит на batch-задачах через OSS self-hosted, и даёт единый интерфейс для всех LLM-вызовов платформы (probe, FAQ-gen, schema-gen).

## In scope

- **Единый интерфейс `LLMRouter`:** `async def complete(prompt, task_type, tenant_config) → LLMResponse`.
- **Провайдеры:**
  - **RU-default (content_gen):** GigaChat API + YandexGPT (Yandex Cloud Foundation Models). Используются для FAQ-генерации (P6) и других content-задач с данными клиентов.
  - **OSS self-hosted (batch-cost):** vLLM + Qwen 2.5 / Saiga (для высокообъёмных batch-задач без ПД клиентов).
  - **Иностранные (opt-in):** OpenAI GPT-4o, Anthropic Claude — только по явному включению тенанта; не для контента с ПД.
  - **Probe-провайдеры:** OpenAI, Anthropic, Perplexity, Yandex Cloud FM, GigaChat API, Gemini API + scraping fallback (отдельный channel в роутере, всегда через зарубежные ноды — NFR-2).
- **Routing-логика:** `task_type` → провайдер по таблице (content_gen → RU-default; probe → geo-aware; batch → OSS). Тенант может override (opt-in иностранные).
- **Uncertainty-статистика:** для probe-канала — агрегация N ≥ 5 прогонов, CI вычисляется в роутере.
- **Cost-guard:** мягкий soft-limit и hard-kill по бюджету (из cost-budget.yaml charter §3.4).
- **Минимизация LangChain/LlamaIndex:** прямые HTTP-клиенты (httpx + tenacity retry); LangChain только если интеграция с конкретным провайдером требует.
- **NFR-3:** контент клиента по умолчанию → RU-провайдеры; иностранные модели — opt-in.

## Out of scope

- Probe-планировщик / Celery-задачи мониторинга (→ P5).
- FAQ-генерация контента (→ P6).
- Embeddings (→ стаб, реальная нагрузка → P6+).
- Yandex Cloud Foundation Models полная интеграция (кроме GigaChat/YandexGPT endpoints).

## Functional requirements

- **NFR-3 (LLM-router):** provider-agnostic абстракция; content_gen по умолчанию RU (GigaChat/YandexGPT); OSS self-hosted (Qwen 2.5 / Saiga via vLLM) для batch-cost; иностранные модели — opt-in для не-чувствительных задач. Минимизировать vendor lock-in (LangChain/LlamaIndex — минимально).

## Acceptance criteria

- **AC-1 (routing):** `task_type=content_gen` без override → вызов идёт в GigaChat/YandexGPT (verify via mock + тест).
- **AC-2 (opt-in иностранные):** тенант с `llm_provider_override=openai` → вызов идёт в OpenAI; тенант без override → OpenAI не вызывается никогда для content_gen.
- **AC-3 (OSS fallback):** при `task_type=batch` → роутинг в vLLM endpoint; тест с mock vLLM.
- **AC-4 (probe dual-geo):** probe-канал всегда использует зарубежный endpoint (mock-тест: RU-IP не используется для ChatGPT/Perplexity — NFR-2, инвариант §6 charter).
- **AC-5 (retry/fault isolation):** provider timeout → retry с tenacity (3 попытки, exponential backoff); сбой одного провайдера не роняет батч — логируется, остальные обрабатываются.
- **AC-6 (cost-guard):** при превышении `per_task: hard $1.50` — задача отменяется, логируется warning.
- **AC-7 (uncertainty):** при N=5 прогонах probe-канала возвращается `{mean, ci_lower, ci_upper}` (проверено unit-тестом с deterministic mock).

## Contracts touched

- **`llm-router` context:** `LLMRouter` class + `complete()` интерфейс; `provider_configs` таблица (tenant_id, task_type, provider, enabled); эмит `llm.call.completed` (для cost-tracking). Стаб расширяется JIT.
- Используется: `probe` context (P5), `recommendations` context (P6).
- NFR-2 инвариант зафиксирован в контракте: probe к ChatGPT/Perplexity — только через зарубежные ноды.

## Exit-gate

| Критерий | Порог |
|---|---|
| Routing по task_type | AC-1..3 пройдены |
| RU-default enforcement | AC-2 (нет иностранных без opt-in) |
| Probe dual-geo | AC-4 пройден (NFR-2) |
| Retry/fault isolation | AC-5 пройден |
| Cost-guard | AC-6 пройден |
| Uncertainty агрегация | AC-7 пройден |
| Аудит tier 4 | PASS (5 линз: correctness · security · compliance · tests · architecture) |

## Decomposition hints for planner

1. `llm-router-specialist` (Opus) проектирует архитектуру роутера, таблицу routing-правил, интерфейс.
2. `llm-router-specialist` реализует httpx-клиенты для GigaChat API, YandexGPT, vLLM endpoint, OpenAI, Perplexity.
3. `backend-implementer` создаёт Alembic-миграцию `provider_configs`, интеграцию с Celery.
4. `tester` пишет unit-тесты с mock-провайдерами для каждого routing-правила + uncertainty-агрегации.
5. `compliance-152fz-specialist` (Opus) ревьюит: routing для content_gen с ПД клиентов → только RU-провайдеры.
6. Полный 5-линзовый аудит (`auditor`/Opus) — обязателен (tier 4, инфра-компонент).
