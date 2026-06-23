# llm-router-specialist — memory

## Namespace

`memory/llm-router-specialist.md`

## MUST-persist

- **Provider registry**: список активных провайдеров, их sensitivity_allowed, cost/token, latency p50/p95
- **Fallback-цепочки** (текущие; версионированы)
- **Routing-решения** (compliance-вердикты от `compliance-152fz-specialist` по каждому провайдеру)
- **vLLM конфиг**: модели (Qwen 2.5 / Saiga), GPU/CPU ресурсы, batch-параметры
- **Известные API-изменения** провайдеров (breaking changes, deprecations)

## MUST-NOT persist

- API-ключи провайдеров (только в Vault/Lockbox)
- Контент запросов клиентов

## Retrieval queries

- «Текущий provider registry с sensitivity_allowed»
- «Compliance-вердикты по провайдерам»
- «Fallback-цепочка для [task_type]»

## Write triggers

- После добавления нового провайдера.
- После compliance-вердикта → обновить sensitivity_allowed.
- При изменении cost/latency характеристик.

## Pruning

- Устаревшие провайдеры (deprecated) → архивировать, не удалять (аудиторский след).
