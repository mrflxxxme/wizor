# cms-connector-specialist — tools allowlist

## Allowed

| Tool | Scope |
|---|---|
| `Read` | `connectors/`, `src/autofix/`, `src/patches/`, `db/migrations/`, `.planning/` |
| `Write` | `connectors/wordpress/`, `src/autofix/`, `api/wp-connector.yaml` |
| `Edit` | те же пути что Write |
| `Grep` | весь repo |
| `Glob` | весь repo |
| `Bash` | `php -l` (синтакс-чек WP plugin); `python -m pytest connectors/`; read-only |
| `WebFetch` | `https://developer.wordpress.org/rest-api/*`, `https://www.indexnow.org/*` |

## Denied

- Прямое чтение WP API credentials (только через Vault env).
- `Write`/`Edit` на `src/iam/`, `src/billing/`, `src/scoring/`, `infra/`.
- Мутация audit log таблицы (только INSERT через ORM).
- `Bash` с деплоем или `git push`.
