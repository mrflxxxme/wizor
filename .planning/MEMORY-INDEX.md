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
| executable-layer | исполняемый слой харнесса | `decisions/ADR-0020` · `.claude/commands/` · `.claude/autonomy/settings.recommended.json` | slash-команды + SessionStart-хук авто-контекста + permission-allowlist + role-loader (спавн из `<role>/`-доков без дублей) | 2026-07-03 |
| autonomy-runner | автономный многофазный runner | `decisions/ADR-0021` · `.claude/autonomy/README.md` · `.claude/commands/autonomy/` | порт ORIION ADR-037: gate-authority merge, 8 решений D1–D8; машина ВЫКЛ, вооружается founder'ом | 2026-07-03 |
| tripwire | задняя растяжка автономии | `.claude/autonomy/tripwire.yaml` · `scripts/autonomy/classify_tripwire.py` | 8 категорий (5 ORIION + WIZOR: autofix/probe-geo/ПДн) → НЕ auto-merge → 1-клик `/ack` | 2026-07-03 |
| evidence-protocol | коммит-привязанный evidence | `.claude/autonomy/evidence-schema.json` · `scripts/autonomy/verify_evidence.py` · `.github/workflows/evidence.yml` | усиливает live-gold ADR-0018 до неподделываемого (head_sha == PR head, freshness=зубы) | 2026-07-03 |
| escalation | передняя растяжка + judge | `.claude/autonomy/escalation-policy.md` · `judge-panel.md` · `_session-context/DECISIONS-LOG.md` | агент владеет impl+arch (decide+log); эскалирует только продукт/рынок + tripwire; широкие форки → judge-панель (auditor) | 2026-07-03 |
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
| p2-crawler | P2 crawler/аудит (код) | `backend/src/wizor/crawler/` · `roadmap/P02-crawler-audit.md` · `PLAN.md` | read-only краулер httpx+Playwright+lxml + rdflib schema-валидатор + crawl_results + Celery crawl_site + POST /sites/{id}/crawl; первая фаза новой методологией (0 эскалаций); verify 88% | 2026-07-05 |
| read-only-guard | структурный read-only + SSRF-блок | `crawler/guard.py` · `crawler/fetch.py` | httpx ReadOnlyTransport (raise на не-GET) + Playwright page.route abort не-GET в тот же guard; private-IP/metadata (169.254.169.254) блок на каждом hop; @context offline (§6.1 структурно, не by-convention) | 2026-07-05 |
| crawl-results | схема crawl_results | `crawler/models.py` · `migrations/versions/0002_crawl_results.py` | TenantMixin §6.8 (tenant_id+FK+index), JSONB pages/audit_summary/schema_validation; потребляет P3 Score | 2026-07-05 |
| methodology-pilot | P2 = пилот автономной методологии | `_session-context/AUDIT-2026-07-05-P2/` · `DECISIONS-LOG.md` · JOURNAL 2026-07-05 | review+audit независимо поймали read-only-bypass (Playwright) + SSRF до мёржа; DTO-шов убрал integration-race; методология окупилась | 2026-07-05 |
| p3-scoring | P3 AI-Readiness Score (код) | `backend/src/wizor/scoring/` · `roadmap/P03-readiness-score.md` | детерминированный ScoringEngine (чистая fn) + ProjectionEngine + score_results (миграция 0003) + `GET /score`; веса geo; verify 90 тестов/89.5% | 2026-07-05 |
| score-weights | веса Score + llms.txt-исключение | `scoring/weights.py` · `scoring/WEIGHTS.md` | 10 факторов сумма 100 (json_ld+faq топ); **llms.txt структурно вне Score §6.5** (EXCLUDED_FROM_SCORE + import-time raise-guard); deferred вне числителя+знаменателя; SCORE_VERSION | 2026-07-05 |
| determinism | детерминизм + honest-forecast паттерн | `scoring/engine.py` · `projection.py` | Score = чистая fn над WEIGHTS-tuple (клок инжектится); проекция = детерминированная дельта на копии, НЕ гарантия Visibility (§6.2); инвариант enforced by construction, не фильтром | 2026-07-05 |
| patterns | паттерны/pitfalls агентов | `.claude/agents/<role>/memory.md` | заполняется по ходу фаз | — |
