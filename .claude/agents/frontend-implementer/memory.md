# frontend-implementer — memory

**namespace:** `agent-memory:frontend-implementer`
**owned files:** `src/` frontend (совместно с git); `tests/` frontend-тесты

## MUST-persist
- Паттерны Next.js/React/shadcn, выявленные в фазах
- API mock-схемы для STUB-контрактов (временные, до заполнения)
- Self-audit failures по типу (TS-ошибки, PII-лог, read-only-нарушения)

## MUST-NOT
- Secrets, публичные env-ключи
- Полные компоненты (только pointer)
- Дизайн-решения без явного AC из spec

## Retrieval queries
- `tag:pattern lang:typescript ctx:<name>` — паттерны компонентов
- `tag:mock-api ctx:<name>` — временные mock-схемы для STUB
- `tag:pitfall topic:nextjs` — известные ошибки Next.js routing/SSR

## Pruning
Mock-схемы → удалять после заполнения реального контракта. Паттерны устаревших shadcn-компонентов → обновлять при смене версии.
