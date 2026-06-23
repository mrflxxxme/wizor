# memory-curator — tools allowlist

## Allowed
- `Read` — все owned-файлы + аудит-отчёты + хендоффы
- `Write` / `Edit` — `.planning/STATUS.md`, `.planning/HANDOFF.md`, `.planning/JOURNAL.md`, `.planning/MEMORY-INDEX.md`, `.planning/memory.md`, `.planning/gates/<id>.md`, `README.md` (статус-блок), `_session-context/archive/`
- `Bash` — `mv` (ротация JOURNAL/AUDIT в archive), `wc -l` (проверка длины JOURNAL)
- `Glob` / `Grep` — поиск в `.planning/` и `_session-context/`

## Denied
- Write/Edit на `src/` или `tests/` — не правит код
- Write на `.planning/decisions/ADR-*.md` (→ architect)
- Write на `revisions/` или `_session-context/VERIFY-*` / `AUDIT-*` активных (только архив)
- Чтение secrets-файлов (`.env`, `*.key`)
- Хранение полного кода или diff в owned-файлах
