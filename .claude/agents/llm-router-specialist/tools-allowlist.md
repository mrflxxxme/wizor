# llm-router-specialist — tools allowlist

## Allowed

| Tool | Scope |
|---|---|
| `Read` | `src/llm_router/`, `config/`, `.planning/`, `memory/llm-router-specialist.md` |
| `Write` | `src/llm_router/`, `src/llm_router/adapters/`, `src/llm_router/config.yaml` |
| `Edit` | те же пути что Write |
| `Grep` | весь repo |
| `Glob` | весь repo |
| `Bash` | `python -m pytest src/llm_router/`; read-only |
| `WebFetch` | документация провайдеров (GigaChat, Yandex Cloud FM, OpenAI-compatible) |

## Denied

- Прямое чтение API-ключей (только через env/Vault).
- `Write` на `src/iam/`, `src/billing/`, `src/crawler/`, `infra/`.
- LangChain-heavy: только тонкие HTTP-адаптеры.
- `Bash` с установкой пакетов (`pip install`).
