# geo-domain-expert — tools allowlist

## Allowed

| Tool | Scope |
|---|---|
| `Read` | `src/scoring/`, `src/recommendations/`, `src/patches/`, `crawler/`, `probe/`, `.planning/` |
| `Write` | `src/scoring/`, `src/recommendations/`, `src/patches/`, `reports/` |
| `Edit` | те же пути что Write |
| `Grep` | весь repo (read-only поиск) |
| `Glob` | весь repo |
| `Bash` | `python -m pytest src/scoring/`; `python -c "import json; ..."` (валидация JSON-LD); read-only |
| `WebFetch` | `https://schema.org/*`, `https://developers.google.com/search/*`, `https://aeoengine.ai/*`, `https://seranking.com/*` |

## Denied

- `Bash` с мутирующими командами (git commit, rm, install).
- `Write`/`Edit` на `src/iam/`, `src/billing/`, `src/connectors/`, `infra/`.
- Любой инструмент, читающий или пишущий secrets/credentials.
- `Write` на `.planning/decisions/` (только `architect` пишет ADR).
