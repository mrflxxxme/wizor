# crawler-probe-specialist — tools allowlist

## Allowed

| Tool | Scope |
|---|---|
| `Read` | `src/crawler/`, `src/probe/`, `config/` (без secrets), `.planning/` |
| `Write` | `src/crawler/`, `src/probe/`, `crawler/` (data output), `probe/` (data output) |
| `Edit` | те же пути что Write |
| `Grep` | весь repo |
| `Glob` | весь repo |
| `Bash` | `python -m pytest src/crawler/`; `python -m pytest src/probe/`; `curl -s https://api.ipify.org` (IP-проверка probe-нод); read-only git команды |
| `WebFetch` | публичные URL сайтов клиентов и конкурентов (scope ограничен задачей) |

## Denied

- Прямое чтение/запись Vault/Lockbox (только через env-переменные).
- `Write` на `src/scoring/`, `src/recommendations/`, `src/iam/`, `infra/`.
- `Bash` с деплоем или изменением инфры.
- Хранение proxy credentials в любом файле repo.
