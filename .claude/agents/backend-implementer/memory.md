# backend-implementer — memory

**namespace:** `agent-memory:backend-implementer`
**owned files:** `src/` backend (совместно с git); `tests/` backend-тесты

## MUST-persist
- Паттерны FastAPI/SQLAlchemy, выявленные в фазах (pitfalls и best-practices)
- Список контракт-стабов, помеченных STUB (блокеры)
- Self-audit failures и их причины (→ не повторять)

## MUST-NOT
- Secrets, env-значения, credentials
- Полные реализации (только pointer на файл + gist)
- Бизнес-логика вне scope задачи

## Retrieval queries
- `tag:pattern lang:python ctx:<name>` — паттерны для конкретного контекста
- `tag:pitfall topic:sqlalchemy` — известные ошибки SQLAlchemy
- `tag:contract-stub status:pending` — незаполненные стабы-блокеры

## Pruning
Паттерны старше 3 фаз без использования → удаляй из namespace. Актуальные → держи компактно (1 паттерн = 3–5 строк max).
