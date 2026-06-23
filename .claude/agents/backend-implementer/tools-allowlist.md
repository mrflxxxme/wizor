# backend-implementer — tools allowlist

## Allowed
- `Read` — `src/`, `tests/`, `.planning/PLAN.md`, контракты, ADR
- `Write` / `Edit` — `src/` (backend only), `tests/` (backend only)
- `Bash` — `pytest`, `ruff`, `mypy`, `alembic` (миграции); НЕ pip install без явного AC
- `Glob` / `Grep` — поиск по `src/` и `tests/`

## Denied
- Write/Edit на `src/` frontend (Next.js/React файлы)
- Write на `.planning/` (кроме чтения)
- Write на `STATUS/HANDOFF/JOURNAL/MEMORY-INDEX` (→ memory-curator)
- `Bash` с `git push`, `git merge`, внешние HTTP-запросы
- Hardcode secrets в любом Write/Edit
