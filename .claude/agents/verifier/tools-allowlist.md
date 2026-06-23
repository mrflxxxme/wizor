# verifier — tools allowlist

## Allowed
- `Read` — `src/`, `tests/`, `.planning/PLAN.md`, phase-spec (exit-gate)
- `Write` — `_session-context/VERIFY-<phase>-<ts>.md`
- `Bash` — `pytest`, `npm test` (запуск тестов, read-only на данных)
- `Glob` / `Grep` — поиск тестовых файлов и AC

## Denied
- Write/Edit на `src/` или `tests/` — не правит тесты
- Write на `.planning/` (кроме чтения PLAN.md)
- Write на `STATUS/HANDOFF/JOURNAL/MEMORY-INDEX` (→ memory-curator)
- `Bash` с деструктивными операциями (drop, delete, external HTTP)
- Субъективные вердикты — только бинарный PASS/FAIL
