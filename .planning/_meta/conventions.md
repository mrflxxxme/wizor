<!-- HEAD-SUMMARY (≤500т): Конвенции WIZOR — Python 3.12/FastAPI/ruff/mypy, TypeScript strict, <500 строк/файл, Conventional Commits, ветки phase/PNN-slug, tier-review (Tier 1–2 авто-мердж, Tier 3+ founder), 11 CI-гейтов, DoD. Не дублировать в phase-файлах — ссылаться. -->

# Conventions — код, тесты, процесс

> Не повторять в phase-файлах. Нарушение convention = обоснование в фазе + ADR.

## Python (backend)

| Аспект | Правило |
|---|---|
| Версия | Python 3.12+; `match`, type hints везде |
| Форматтер | `ruff format` — auto в pre-commit |
| Линтер | `ruff check --select=ALL` (конфиг в `pyproject.toml`) |
| Type checker | `mypy --strict` для `src/`; тесты без `--strict` |
| Тесты | `pytest` + `pytest-asyncio` + `pytest-cov`; coverage ≥70% / ≥85% security-critical |
| Async | `httpx`, `asyncpg`, `redis.asyncio`; никаких блокирующих вызовов в async |
| Pydantic | v2; модели — единственная граница типов между слоями |
| Структура | Модульный монолит: `src/<bounded_context>/` (13 контекстов из чартера §7) |
| Размер файла | **< 500 строк (хард-лимит)** — split на модули |
| Env / config | Pydantic Settings; никаких magic strings |
| Secrets | Никогда в коде; `.env.example` коммитим, `.env` — нет; Vault / Yandex Lockbox |
| Logging | `structlog` JSON + OpenTelemetry |

## TypeScript (frontend)

| Аспект | Правило |
|---|---|
| Версия | TypeScript 5.x strict |
| Форматтер | Prettier (CI + pre-commit) |
| Линтер | ESLint + `@typescript-eslint/recommended-type-checked` |
| Тесты | Vitest (unit); Playwright (e2e) |
| State | Zustand (global); TanStack Query (server) |
| Стили | Tailwind CSS + shadcn/ui; без CSS-in-JS |
| Размер файла | **< 500 строк** |
| Accessibility | ARIA labels обязательны; контраст WCAG AA |

## Git и PR

| Аспект | Правило |
|---|---|
| Ветки | `phase/PNN-slug` (фазы); `fix/<slug>` (баги); `hotfix/<slug>` (prod) |
| Commits | **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`); footer `Refs: PNN, ADR-NNNN` |
| PR title | `[PNN] <описание>` |
| Размер PR | < 500 строк (исключения: генерируемый код, миграции) |
| Merge | squash-merge |

## Tier-based review

Founder — **единственный человек-апрувер Tier 3+** (чартер §2 #10):

| Tier | Примеры | Апрувер | Авто-мердж |
|---|---|---|---|
| 1–2 | Docs, config, лёгкий UI | AI (`reviewer`) | Да, зелёный CI |
| 3 | Crawler, scoring, probe, recommendations, verification | **Founder** | Нет |
| 4 | Инфра, billing, Keycloak, auto-fix, ПДн | **Founder** | Нет |

Security / compliance / ПДн любого уровня → всегда Founder + эскалация к `architect`.

## CI gates (обязательно для каждого PR)

```
1.  Lint           ruff, eslint
2.  Type-check     mypy --strict, tsc --strict
3.  Unit tests     pytest / vitest + coverage
4.  Integration    pytest + testcontainers (Postgres 16, Redis 7)
5.  Security SAST  Semgrep + Bandit
6.  Secrets scan   gitleaks
7.  Dep scan       pip-audit + npm audit
8.  SBOM           Syft + Grype
9.  License scan   запрет GPL/AGPL
10. Container scan Trivy
11. Migration      squawk
```

Fail = блок merge. Bypass = explicit override + founder + ADR.

## Definition of Done (фаза)

- [ ] Все tasks done; все AC выполнены и покрыты тестами
- [ ] CI зелёный, coverage gate пройден
- [ ] Документация обновлена (README, OpenAPI, runbook)
- [ ] ADR создан/обновлён при значимых решениях
- [ ] Контракты bounded-context соблюдены и обновлены
- [ ] Память обновлена (`memory-curator`: STATUS/HANDOFF/JOURNAL/MEMORY-INDEX)
- [ ] Gate заполнен / обновлён для текущей фазы
- [ ] Handoff записан (чартер §8.6)
- [ ] PR апрувнут по tier-таблице и смерджен
