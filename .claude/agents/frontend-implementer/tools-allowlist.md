# frontend-implementer — tools allowlist

## Allowed
- `Read` — `src/`, `tests/`, `.planning/PLAN.md`, контракты, ADR
- `Write` / `Edit` — `src/` (frontend only: .tsx, .ts, .css), `tests/` (frontend only)
- `Bash` — `npm run build`, `npm run lint`, `npm test`; НЕ npm install без явного AC
- `Glob` / `Grep` — поиск по `src/` frontend и `tests/`

## Denied
- Write/Edit на `src/` backend (Python файлы, alembic)
- Write на `.planning/` (кроме чтения)
- Write на `STATUS/HANDOFF/JOURNAL/MEMORY-INDEX` (→ memory-curator)
- `Bash` с `git push`, `git merge`, внешние HTTP-запросы
- Hardcode secrets, публичные API-ключи в коде
