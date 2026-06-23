# devops-infra-specialist — tools allowlist

## Allowed

| Tool | Scope |
|---|---|
| `Read` | `infra/`, `ci/`, `.github/`, `docker-compose*.yml`, `Dockerfile*`, `.planning/` |
| `Write` | `infra/`, `ci/`, `.github/workflows/`, `docker-compose*.yml`, `Dockerfile*` |
| `Edit` | те же пути что Write |
| `Grep` | весь repo |
| `Glob` | весь repo |
| `Bash` | `docker build`; `kubectl get/describe`; `git status/diff/log`; `curl -s https://api.ipify.org`; `yc` (read-only); `vault read` |
| `WebFetch` | `https://cloud.yandex.ru/docs/*`, `https://docs.hetzner.com/*`, `https://www.vaultproject.io/docs/*` |

## Denied
- `Write`/`Edit` на `src/` (исходный код приложения)
- `git commit`, `git push`; secrets в файлах repo
- `docker push` без CI; `kubectl delete` без founder-задачи
