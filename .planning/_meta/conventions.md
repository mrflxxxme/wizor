<!-- HEAD-SUMMARY (≤500т): Конвенции WIZOR — Python 3.12/FastAPI/ruff/mypy, TypeScript strict, <500 строк/файл, Conventional Commits, ветки phase/PNN-slug, tier-review (tier задаёт строгость CI/аудита; human-аппрув только на гейте фазы — ADR-0017), 11 CI-гейтов, DoD. Не дублировать в phase-файлах — ссылаться. -->

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
| Состояние PR | **открыт (ready-for-review), НЕ draft** — после пуша чеки/AI-ревью стартуют сразу; агент чинит фейлы автономно; founder получает только итог (ADR-0019) |
| Размер PR | < 500 строк (исключения: генерируемый код, миграции) |
| Merge | squash-merge |

## Tier-based review

**Human-аппрув — только на гейте фазы** (`founder_signature`, ADR-0017). Внутри фазы PR авто-мерджятся на (зелёный CI + `reviewer` APPROVE + `auditor` PASS). Tier задаёт глубину аудита и строгость CI, НЕ маршрутизацию на человека:

| Tier | Примеры | Аудит (шаг 7) | CI |
|---|---|---|---|
| 1–2 | Docs, config, лёгкий UI | 1 линза | базовый |
| 3 | Crawler, scoring, probe, recommendations, verification | 3 линзы | полный |
| 4 | Инфра, billing, Keycloak, auto-fix, ПДн | 5 линз | полный + security |

Security / compliance / ПДн любого уровня → обязательная линза `auditor` + эскалация к `architect`/founder при реальном блокере. Необратимые ВНЕШНИЕ действия (реальный prod, деньги, DPA) — отдельный product-runtime consent (ADR-0015), не dev-ревью.

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
- [ ] **Live-gold пройден** (end-to-end против реальных сервисов) ИЛИ явный `deferred_live_gold` в гейте с обоснованием (ADR-0018)
- [ ] Документация обновлена (README, OpenAPI, runbook)
- [ ] ADR создан/обновлён при значимых решениях
- [ ] Контракты bounded-context соблюдены и обновлены
- [ ] Память обновлена (`memory-curator`: STATUS/HANDOFF/JOURNAL/MEMORY-INDEX)
- [ ] Gate заполнен / обновлён для текущей фазы
- [ ] Handoff записан (чартер §8.6)
- [ ] PR авто-смерджен (CI + reviewer + auditor PASS); гейт фазы подписан founder при закрытии фазы
