# planner — tools allowlist

## Allowed
- `Read` — phase-spec, contracts, ADR, STATUS, HANDOFF, MEMORY-INDEX
- `Write` — `.planning/PLAN.md` (единственный output)
- `Glob` — поиск файлов в `.planning/`
- `Grep` — поиск по контрактам и ADR

## Denied
- `Bash` — не запускает команды
- `Edit` — не редактирует src/ код
- `Agent` — не спавнит суб-агентов (только founder через 9-шаговый цикл)
- Любые write-операции вне `.planning/PLAN.md`
