# cms-connector-specialist — memory

## Namespace

`memory/cms-connector-specialist.md`

## MUST-persist

- **WP plugin версии**: текущая + история (совместимость с WP-версиями)
- **Известные WP-quirks**: темы/плагины, конфликтующие с JSON-LD в `<head>`
- **Idempotency паттерны**: хэш-стратегия для каждого типа патча
- **Rollback-паттерны**: что хранить в снапшоте для каждого типа правки
- **IndexNow timing**: задержки между apply и пингом (эмпирика)

## MUST-NOT persist

- WP API credentials (только Vault/Lockbox)
- Содержимое audit log (хранится в БД, не в памяти агента)
- Контент сайтов клиентов

## Retrieval queries

- «Известные конфликты с [тема/плагин]»
- «Idempotency стратегия для [тип патча]»

## Write triggers

- После каждой P10 задачи: обновить quirks и паттерны.
- `memory-curator` пишет после шага 8.

## Pruning

- WP-quirks для версий WP < 5.x → архивировать.
