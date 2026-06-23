# reviewer — tools allowlist

## Allowed
- `Read` — весь проект (read-only на src/)
- `Write` — `revisions/<phase>-*.md` (только findings-файлы)
- `Glob` / `Grep` — поиск по src/, tests/, контрактам, ADR
- `Bash` — `git diff`, `git log` (read-only git)

## Denied
- Write/Edit на `src/` или `tests/` — не правит код
- Write на `.planning/PLAN.md`, `STATUS`, `HANDOFF` (→ planner/memory-curator)
- Write на ADR (→ architect)
- `Bash` с тест-запуском или CI-командами (→ verifier)
- Approve без запуска `checklists/pr-review.md`
