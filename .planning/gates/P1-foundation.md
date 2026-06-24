---
gate: P1-foundation
status: pending
opened_at: "2026-06-24"
closed_at: null
founder_signature: null

hard_thresholds:
  backend_coverage:
    target: 70
    actual: 86.81
    passed: true
    evidence_url: ".planning/_session-context/VERIFY-P1-2026-06-24.md#tests"
    measured_at: "2026-06-24"
    description: "AC-2: backend unit-покрытие ≥70%. Измерено локально pytest -m 'not integration' = 86.81%."
  frontend_coverage:
    target: 70
    actual: 100
    passed: true
    evidence_url: ".planning/_session-context/VERIFY-P1-2026-06-24.md#tests"
    measured_at: "2026-06-24"
    description: "AC-2: frontend vitest-покрытие ≥70%. Измерено локально = 100% lines."
  lint_type_sast:
    target: "green"
    actual: "green"
    passed: true
    evidence_url: ".planning/_session-context/VERIFY-P1-2026-06-24.md#tests"
    measured_at: "2026-06-24"
    description: "ruff + mypy --strict + bandit (backend), eslint + tsc (frontend) — все зелёные локально."
  ci_pipelines_green:
    target: "green"
    actual: "green"
    passed: true
    evidence_url: "https://github.com/mrflxxxme/wizor/actions/runs/28076492564"
    measured_at: "2026-06-24"
    description: "AC-3: workflow backend(quality+integration+keycloak-smoke)/frontend/security зелёные на коммите 76641f6. Все jobs success, каждый ≤8 мин."
  multitenant_isolation:
    target: 0
    actual: 0
    passed: true
    evidence_url: "https://github.com/mrflxxxme/wizor/actions/runs/28076492564"
    measured_at: "2026-06-24"
    description: "AC-6: cross-tenant утечки нет (0 чужих строк). Live-gold: CI integration job success (pgvector pg16, тест second-tenant)."
  pgvector_active:
    target: 3
    actual: 3
    passed: true
    evidence_url: "https://github.com/mrflxxxme/wizor/actions/runs/28076492564"
    measured_at: "2026-06-24"
    description: "AC-8: vector_dims('[1,2,3]'::vector)=3. Live-gold: CI integration job success."
  celery_ping:
    target: "pong"
    actual: "pong"
    passed: true
    evidence_url: "https://github.com/mrflxxxme/wizor/actions/runs/28076492564"
    measured_at: "2026-06-24"
    description: "AC-7: живой Celery worker отвечает на inspect ping. Live-gold: CI integration job success."
  audit_tier4:
    target: "PASS"
    actual: "PASS-WITH-FIXES"
    passed: true
    evidence_url: ".planning/_session-context/AUDIT-2026-06-24-P1/AUDIT-REPORT.md"
    measured_at: "2026-06-24"
    description: "Tier-4 5-линзовый аудит + 10 инвариантов §6 (10/10 PASS/N/A). Блокеров нет; фиксы применены в цикле."
  bootstrap_time:
    target: 600
    actual: null
    passed: null
    evidence_url: ".planning/_session-context/VERIFY-P1-2026-06-24.md#deferred_live_gold"
    measured_at: null
    description: "AC-1: make dev-bootstrap ≤600с. DEFERRED (DLG-2): Docker-демон недоступен в эфемерной сессии; compose валиден, healthchecks/--wait заданы. Founder прогоняет на машине с Docker."
  posthog_ui_event:
    target: "proven"
    actual: "deferred"
    passed: null
    evidence_url: ".planning/_session-context/VERIFY-P1-2026-06-24.md#deferred_live_gold"
    measured_at: null
    description: "AC-5 / FR-P1-1: событие видно в PostHog UI. DEFERRED (DLG-1): self-hosted PostHog (ClickHouse-стек) вне bootstrap-бюджета P1; SDK интегрирован обеими сторонами, no-op оттестирован. Founder поднимает инстанс на P7/проде."

deliverables:
  - id: D1
    name: "Backend: FastAPI (/health,/metrics), config (РФ-резидентность), tenancy, IAM-модели, Alembic+pgvector, Celery, PostHog-абстракция"
    status: done
    owner: "backend-implementer (orchestrator)"
    notes: "10 unit-тестов, cov 86.81%; mypy/ruff/bandit зелёные"
  - id: D2
    name: "Frontend: Next.js 15/React 19/TS strict, Tailwind(shadcn-ready), PostHog-провайдер (no-op), контракт North Star событий, health-страница"
    status: done
    owner: "frontend-implementer (orchestrator)"
    notes: "6 vitest, cov 100%; eslint/tsc зелёные; Next 15.5.19 (CVE-патч)"
  - id: D3
    name: "Infra: docker-compose.dev (pg16+pgvector, redis7, keycloak realm skeleton, backend, celery, frontend, caddy + healthchecks), .env.example RU-only"
    status: done
    owner: "devops-infra-specialist (orchestrator)"
    notes: "docker compose config валиден; live-bootstrap = DLG-2"
  - id: D4
    name: "CI: 3 GitHub Actions workflow (backend+integration live-gold, frontend, security) + Makefile + pre-commit"
    status: done
    owner: "devops-infra-specialist (orchestrator)"
    notes: "live-gold (PG/pgvector/Celery/Keycloak) в CI; статус прогона → ci_pipelines_green"
  - id: D5
    name: "Verify/Audit/Memory: VERIFY-evidence, 5-линзовый AUDIT (PASS-WITH-FIXES), gate-файл, обновление STATUS/HANDOFF/JOURNAL/MEMORY-INDEX"
    status: done
    owner: "verifier + auditor + memory-curator (orchestrator)"
    notes: "review APPROVE-WITH-COMMENTS; audit 10/10 инвариантов"

adr_delta:
  created: []
  revised: []
  superseded: []

risks_delta:
  opened: []
  closed: []
  mitigated: []
  escalated: []
---

# Gate: P1 Foundation (exit-gate фазы)

## Назначение

Exit-gate фазы **P1 (Foundation)** — поднят рабочий dev+CI-стек (monorepo, FastAPI+Postgres/pgvector+Redis+Celery, multi-tenant схема, Keycloak/PostHog skeleton, observability), на который ложатся фазы P2–P10. Tier-4 ⇒ обязателен 5-линзовый аудит. Human-checkpoint = **только этот гейт** (ADR-0017): внутри фазы PR авто-мерджатся на зелёный CI + reviewer + auditor + verify.

## Статус прохождения

| Критерий | Порог | Факт | Статус |
|---|---|---|---|
| Backend coverage (AC-2) | ≥70% | 86.81% | ✅ PASS |
| Frontend coverage (AC-2) | ≥70% | 100% | ✅ PASS |
| Lint/type/SAST | green | green | ✅ PASS (локально) |
| Audit tier-4 (5 линз + §6) | PASS | PASS-WITH-FIXES | ✅ PASS |
| CI 3 workflow (AC-3) | green ≤8мин | green (76641f6) | ✅ PASS |
| Multi-tenant изоляция (AC-6) | 0 утечек | 0 (CI live-gold) | ✅ PASS |
| pgvector (AC-8) | dims=3 | 3 (CI live-gold) | ✅ PASS |
| Celery ping (AC-7) | pong | pong (CI live-gold) | ✅ PASS |
| `make dev-bootstrap` ≤600с (AC-1) | ≤600с | — | ⚠️ DEFERRED (DLG-2: нет Docker в сессии) |
| PostHog UI событие (AC-5) | proven | deferred | ⚠️ DEFERRED (DLG-1: self-host → P7) |

## deferred_live_gold (ADR-0018 — явный, не тихий)

- **DLG-1 — PostHog self-hosted UI:** тяжёлый ClickHouse-стек вне bootstrap-бюджета P1. SDK интегрирован backend+frontend, no-op оттестирован. **Founder action:** поднять self-hosted PostHog + ключ на P7/проде, проверить North Star событие в UI.
- **DLG-2 — `make dev-bootstrap` ≤600с:** Docker-демон недоступен в эфемерной сессии. Compose валиден, healthchecks/`--wait` заданы. **Founder action:** прогнать на машине с Docker, зафиксировать время.

## Founder decision area

CI финального коммита **76641f6** зелёный (все jobs success) — CI-зависимые пороги обновлены (`passed: true`). Остаётся решение founder: принять ли DLG-1 (PostHog self-host→P7) и DLG-2 (`make dev-bootstrap` на машине с Docker) как отложенные, и подписать гейт.

## Sign-off

- **Статус:** pending (готов к подписи — все измеримые пороги PASS, deferred задокументированы)
- **Подпись основателя:** _pending_
- **Дата:** _pending_

> Все hard_thresholds: 7 PASS (coverage×2, lint/type/sast, audit, ci, isolation, pgvector, celery — измерены), 2 deferred (bootstrap, posthog_ui — founder action). Для закрытия: founder ставит `status: passed` + `founder_signature` + `closed_at`.
