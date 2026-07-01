# WIZOR

**AI Readiness Platform для РФ** — делает сайт доступным и понятным для ИИ-поиска (ChatGPT, Perplexity, Алиса/Нейро, GigaChat) и замыкает полный цикл: **Аудит → Мониторинг → Рекомендации → Авто-имплементация → Верификация**.

Этот репозиторий — **не код продукта, а структура планирования**: поэтапное техническое задание (ТЗ) + харнесс команды профильных ИИ-агентов, который это ТЗ исполняет. Разрабатывается соло-фаундером с доменной экспертизой + выделенной командой ИИ-агентов по **файл-нативному, токен-эффективному** воркфлоу (по образцу проекта ORIION, но легче).

> Документ написан **в первую очередь для ИИ-агентов**. Точка входа агента — [`.planning/_meta/BUILD-CHARTER.md`](.planning/_meta/BUILD-CHARTER.md) (источник истины по воркфлоу) и [`.planning/PRD.md`](.planning/PRD.md) (продукт).

<!-- STATUS:BEGIN (авто-обновляется memory-curator на шаге 8 цикла; вручную не править) -->
## 📍 Статус

**Стадия:** P1 Foundation 🟢 реализован (2026-06-24) — monorepo (FastAPI+PG/pgvector+Redis+Celery+Keycloak/PostHog skeleton, multi-tenant, 3 CI workflow); первый продуктовый код.
**Активная фаза:** P1 (ждёт зелёный CI + founder-подпись гейта) · **Следующая:** P2 — Crawler/Аудит, либо P0 — Discovery.
**Действия founder:** подписать [`gates/P1-foundation.md`](.planning/gates/P1-foundation.md) после проверки CI · запустить P0 ([`roadmap/P00-discovery.md`](.planning/roadmap/P00-discovery.md)) · заполнить [`PLACEHOLDERS.md`](.planning/PLACEHOLDERS.md).
<!-- STATUS:END -->

---

## Что внутри

```
wizor/
├── README.md                      ← вы здесь
├── CLAUDE.md                      ← правила харнесса для Claude Code
├── .claude/
│   ├── AGENTS.md                  ← обзор ростера (8 ядро + 6 профильных)
│   └── agents/
│       ├── _shared/               ← cost-budget, handoff-формат, pipeline-шаблоны
│       ├── planner · architect · backend-implementer · frontend-implementer
│       ├── reviewer · verifier · auditor · memory-curator        (ядро, 8)
│       └── geo-domain-expert · crawler-probe-specialist · llm-router-specialist
│           cms-connector-specialist · compliance-152fz-specialist
│           devops-infra-specialist                               (профильные, 6)
└── .planning/
    ├── PRD.md                     ← ТЗ продукта (v0.2)
    ├── _meta/BUILD-CHARTER.md     ← keystone: воркфлоу + форматы + инварианты
    ├── _meta/{conventions,stack,glossary}.md
    ├── PROJECT.md · ROADMAP.md    ← обзор + роадмап P0–P10
    ├── roadmap/P00…P10-*.md       ← детальные phase-spec'ы (goal/scope/FR/AC/gate)
    ├── decisions/ADR-*.md         ← 16 архитектурных решений
    ├── contracts/<13 контекстов>/ ← контракты bounded-context'ов (стабы + JIT)
    ├── gates/                     ← exit-гейты (P0→auto-fix, A→B)
    ├── agent-handbook/00…07.md    ← операционный мануал команды
    ├── STATUS · HANDOFF · JOURNAL · MEMORY-INDEX · PHASE-HISTORY
    └── OPEN-QUESTIONS · PLACEHOLDERS · _session-context/ (пост-аудиты)
```

## Как работает команда ИИ-агентов

**Цикл фазы (9 шагов):** Scope → Plan(pinned) → Domain-build(профильный агент пишет сам) → Implement → Review(≤2 цикла) → Verify → **Post-audit** → **Memory-update** → PR (авто-мердж внутри фазы; человек — только на гейте фазы, ADR-0017).

**Ростер:** лёгкое ядро из 8 агентов (всегда) + 6 профильных, которые спавнятся **только когда фаза касается их домена** (иначе 0 токенов). Оркестратор — founder + главная сессия.

**Тиринг моделей** (главный рычаг экономии токенов): Tier-0 без LLM (тривиальные правки) · Haiku (verifier, memory-curator) · Sonnet (имплементеры, reviewer, специалисты-в-кодинге) · Opus (planner, architect, auditor, судительные специалисты). Эскалация вверх по флагу.

**Память — файл-нативная:** состояние и знания живут как git-markdown в `.planning/`; recall через [`MEMORY-INDEX.md`](.planning/MEMORY-INDEX.md) + summary-first (не векторный поиск); `memory-curator` — единственный писатель; ротация JOURNAL/STATUS с дня 1.

**Пост-аудит обязателен** на каждой фазе, глубина по риск-тиру (1 / 3 / 5 линз) + 10 стоячих продуктовых инвариантов.

Подробно — [`agent-handbook/`](.planning/agent-handbook/) и [`BUILD-CHARTER.md`](.planning/_meta/BUILD-CHARTER.md).

## Роадмап (read-only-first)

Ценность монетизируется рано через read-only-дорожки; авто-имплементация — премиум-апгрейд.

| | Фаза | Track |
|---|---|---|
| **P0** | Discovery & De-risking (H1–H5) | research |
| **P1** | Foundation (multi-tenant, CI, observability) | infra |
| **P2–P3** | Crawler/Аудит + AI-Readiness Score | read-only |
| **P4–P5** | LLM-router + Probe-мониторинг (dual-geo) | read-only |
| **P6** | Рекомендации + competitive gap + патчи + honest forecast | read-only |
| **P7** | ⭐ Tier 0 Instant Audit (no-auth PLG-вход) | read-only |
| **P8** | Верификация (re-crawl proof-loop) | read-only |
| **P9** | Auth + биллинг + дорожки (Manual/Auto) | infra |
| **P10** | ⭐ Auto track: WP-коннектор + auto-fix + DPA *(gated_by P0)* | auto |
| → | **A→B gate** → Phase B (agency) → Phase C (enterprise) | — |

## Ключевые инварианты (проверяются в каждом аудите)

read-only-граница (DPA/API — гейт только Auto track) · honest-forecast (нет гарантированных Visibility-%) · auto-fix идемпотентен + обратим + append-only audit log + DPA · ноль РФ-IP к ChatGPT/Perplexity · llms.txt вне citation-score · ПДн в РФ (152-ФЗ) · uncertainty N≥5+CI · multi-tenant изоляция · секреты не в коде · FAQ не авто-публикуется.

## Как пользоваться

**Founder:** открой [`STATUS.md`](.planning/STATUS.md) → выбери фазу → запусти 9-шаговый цикл (главная сессия = оркестратор, делегирует профильным агентам и при нужде спавнит доп-сессии). **Ревьюишь только гейты фаз** — внутри фазы агенты работают автономно ([ADR-0017](.planning/decisions/ADR-0017-phase-gate-only-autonomy.md)).

**ИИ-агент:** прочитай [`CLAUDE.md`](CLAUDE.md) → [`BUILD-CHARTER.md`](.planning/_meta/BUILD-CHARTER.md) → свою папку `.claude/agents/<role>/` → phase-spec → работай. Не грузи контекст превентивно.

---

*Сборка: 2026-06-23 · харнесс по образцу ORIION, оптимизирован под токен-эффективность. Изменения воркфлоу — только через ADR.*
