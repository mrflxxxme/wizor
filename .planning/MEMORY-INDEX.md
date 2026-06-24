<!-- HEAD-SUMMARY (≤500т): Курируемый индекс памяти WIZOR для дешёвого recall. Агент читает этот индекс → грузит полный файл ТОЛЬКО при попадании по тегу. Не векторный поиск — детерминированные указатели. Ведёт memory-curator (шаг 8). -->

# MEMORY-INDEX — WIZOR

> Recall-протокол: найди тег → открой указанный `file:section`. Не грузи всё подряд.

| tag | topic | pointer | gist | updated |
|---|---|---|---|---|
| substrate | файл-нативный субстрат | `decisions/ADR-0001` | агенты=Agent tool, память=git-файлы, claude-flow опц. | 2026-06-23 |
| roster | состав агентов | `_meta/BUILD-CHARTER.md` §3 · `.claude/AGENTS.md` | 8 ядро + 6 профильных по требованию | 2026-06-23 |
| tiering | модели по роли | `decisions/ADR-0003` · charter §3.3 | Tier-0/Haiku/Sonnet/Opus + эскалация | 2026-06-23 |
| loop | цикл фазы | charter §4 · `agent-handbook/07-AI-TEAM-PIPELINE.md` | 9 шагов, обяз. пост-аудит+память | 2026-06-23 |
| autonomy | автономия / gate-only | `decisions/ADR-0017` · charter §11 · CLAUDE.md · `agent-handbook/02-DELEGATION.md` | человек только на гейтах; per-PR авто-мердж; доп-сессии (Agent tool / claude -p) + контекст-менеджмент | 2026-06-23 |
| testing | тесты + live-gold перед PR | `decisions/ADR-0018` · charter §12 · `.claude/agents/verifier/` | self-run unit+integration + live-gold (где возможно); evidence в гейт; deferred_live_gold если невозможно | 2026-06-23 |
| pr-state | PR открыт, не draft | `decisions/ADR-0019` · charter §4 шаг 9 · CLAUDE.md Git/PR | PR создаётся сразу open (ready-for-review); чеки/ревью немедленно; фейлы чинятся в цикле; founder видит итог | 2026-06-24 |
| audit | пост-аудит | `decisions/ADR-0005` · charter §6 · `.claude/agents/auditor/` | риск-тир 1/3/5 линз + 10 инвариантов | 2026-06-23 |
| invariants | стоячие инварианты | charter §6 · `auditor/checklists/invariant-checklist.md` | read-only, honest-forecast, auto-fix-safety… | 2026-06-23 |
| memory | память/recall | `decisions/ADR-0006` · charter §10 | MEMORY-INDEX + summary-first + ротация | 2026-06-23 |
| roadmap | фазы P0–P10 | `ROADMAP.md` · `roadmap/P0*.md` | read-only-first, auto-fix=P10 апгрейд | 2026-06-23 |
| access-model | Tier0/Manual/Auto | `decisions/ADR-0012` · PRD §4.1 | DPA/API гейт только Auto track | 2026-06-23 |
| contracts | bounded contexts | `contracts/README.md` · charter §7 | 13 контекстов, стабы+JIT | 2026-06-23 |
| gates | гейты фаз | `gates/` · charter §8.5 | P0→auto-fix, A→B; JSON-schema | 2026-06-23 |
| stack | тех-стек | `_meta/stack.md` · `decisions/ADR-0011` · PRD §12 | Python/FastAPI, Next.js, PG+pgvector, Keycloak | 2026-06-23 |
| compliance | 152-ФЗ/ПДн/DPA | `decisions/ADR-0015` · `.claude/agents/compliance-152fz-specialist/` | резидентность РФ, DPA, audit-log | 2026-06-23 |
| scoring | AI-Readiness Score | `roadmap/P03-readiness-score.md` · PRD FR-1.3 | детерминир., llms.txt вне веса | 2026-06-23 |
| probe | dual-geo probe | `roadmap/P05-probe-monitoring.md` · ADR-0014 | N≥5+CI, ноль РФ-IP к ChatGPT/Perplexity | 2026-06-23 |
| autofix | auto-fix/trust-ladder | `roadmap/P10-auto-track.md` · ADR-0015 | идемпотентно, rollback, DPA, FAQ не-авто | 2026-06-23 |
| conventions | конвенции кода/git | `_meta/conventions.md` | Conventional Commits, tier-review, CI, DoD | 2026-06-23 |
| glossary | термины | `_meta/glossary.md` | продукт + харнесс термины | 2026-06-23 |
| open-questions | открытые вопросы | `OPEN-QUESTIONS.md` · PRD §16 | 9 гипотез/вопросов к валидации | 2026-06-23 |
| placeholders | TBD-токены | `PLACEHOLDERS.md` | ключи/юрлицо/инфра до прода | 2026-06-23 |
| p1-foundation | P1 фундамент (код) | `backend/` · `frontend/` · `infra/` · `gates/P1-foundation.md` | monorepo: FastAPI+PG/pgvector+Redis+Celery+Keycloak/PostHog skeleton, multi-tenant (TenantMixin §6.8), 3 CI workflow; первый продуктовый код | 2026-06-24 |
| tenancy | multi-tenant паттерн | `backend/src/wizor/core/tenancy.py` · `db/base.py` (TenantMixin) | X-Tenant-Id→request.state.tenant_id (P9: JWT); tenant_id+FK+index на каждой таблице; изоляция на app-level | 2026-06-24 |
| ci-live-gold | CI как раннер live-gold | `.github/workflows/backend.yml` (job integration) | живой smoke PG/pgvector/Redis/Celery/Keycloak в CI; CI-лог = evidence_url; Docker в сессии недоступен | 2026-06-24 |
| analytics | PostHog no-op паттерн | `backend/.../analytics/posthog.py` · `frontend/lib/analytics.ts` | пустой ключ → no-op; North Star событие-константы — контракт backend↔frontend; self-host deferred→P7 | 2026-06-24 |
| patterns | паттерны/pitfalls агентов | `.claude/agents/<role>/memory.md` | заполняется по ходу фаз | — |
