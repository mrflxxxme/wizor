# compliance-152fz-specialist — tools allowlist

## Allowed

| Tool | Scope |
|---|---|
| `Read` | весь repo (read-only аудит) |
| `Write` | `memory/compliance-152fz-specialist.md`, `reports/compliance-*.md`, `checklists/` |
| `Edit` | те же пути что Write |
| `Grep` | весь repo |
| `Glob` | весь repo |
| `WebFetch` | `https://rkn.gov.ru/*`, `https://clck.ru/*` (РКН-нормативные документы), `https://consultant.ru/*` |

## Denied

- `Write`/`Edit` на `src/` (код не пишет; только compliance-вердикты и документы).
- `Write`/`Edit` на `.planning/decisions/` (ADR пишет только `architect`).
- Прямое чтение или запись secrets/credentials.
- `Bash` (не нужен для compliance-задач; при необходимости эскалация к `architect`).
