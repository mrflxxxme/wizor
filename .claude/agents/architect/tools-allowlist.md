# architect — tools allowlist

## Allowed
- `Read` — любой файл проекта (read-only на src/)
- `Write` — `.planning/decisions/ADR-*.md`; `.planning/contracts/<ctx>/README.md`; `.planning/gates/<id>.md` (architect-вердикт)
- `Glob` / `Grep` — поиск по всему проекту
- `Edit` — только `.planning/decisions/` и `.planning/contracts/`

## Denied
- `Bash` — не запускает тесты или CI
- `Edit` на `src/` — не правит production-код
- Write на `STATUS/HANDOFF/JOURNAL/MEMORY-INDEX` (→ memory-curator)
- Merge/push операции
