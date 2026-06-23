# architect — memory

**namespace:** `agent-memory:architect`
**owned files:** `.planning/decisions/ADR-*.md`; `.planning/contracts/<ctx>/README.md` (совместно)

## MUST-persist
- Индекс ADR: `ADR-NNNN → тема → статус` (1 строка/ADR)
- Открытые architectural questions с приоритетом
- Паттерны решений, повторяющихся across фазами

## MUST-NOT
- Полный код
- Secrets
- Продуктовые решения (→ founder)
- Дублирование ADR-текста (только pointer + gist)

## Retrieval queries
- `tag:adr status:accepted` — активные архитектурные решения
- `tag:contract ctx:<name>` — контракт-стабы конкретного контекста
- `tag:escalation topic:security` — паттерны security-эскалаций

## Pruning
ADR со `status: superseded` → помечать, не удалять (историческая ценность). В namespace — только gist + pointer, не полный текст ADR.
