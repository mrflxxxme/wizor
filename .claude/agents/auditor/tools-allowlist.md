# auditor — tools allowlist

## Allowed
- `Read` — весь проект (все артефакты фазы, ADR, контракты, VERIFY-файл)
- `Write` — `_session-context/AUDIT-<date>-<phase>/` (отчёты и линза-файлы)
- `Glob` / `Grep` — глубокий поиск по src/, tests/, config/, secrets-паттернам
- `Bash` — `git log --follow`, `grep -r` для поиска secrets/patterns (read-only)

## Denied
- Write/Edit на `src/` или `tests/` (fix → отдаёт implementer)
- Write на `.planning/decisions/` (→ architect)
- Write на `STATUS/HANDOFF/JOURNAL/MEMORY-INDEX` (→ memory-curator)
- Архивирование аудит-файлов самостоятельно (→ memory-curator)
- Выдача вердикта без проверки всех 10 инвариантов charter §6
