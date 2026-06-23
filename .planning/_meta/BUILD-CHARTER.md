<!-- HEAD-SUMMARY (≤500т): Это keystone-спецификация харнесса WIZOR — файл-нативного, токен-эффективного воркфлоу ИИ-команды (по образцу ORIION, но легче). Содержит: 18 проектных решений, ростер из 8 ядро-агентов + 6 профильных, тиринг моделей, 9-шаговый цикл фазы, роадмап P0–P10 (read-only-first), карту из 13 bounded-context'ов, форматы всех файлов и стоячие инварианты аудита. Любой build-агент читает ЭТОТ файл + .planning/PRD.md перед генерацией. Продукт: AI Visibility / AI Readiness Platform для РФ (аудит→мониторинг→рекомендации→авто-имплементация→верификация). -->

# BUILD-CHARTER — спецификация харнесса разработки WIZOR

> **Назначение.** Единый источник истины для ИИ-агентов, собирающих и развивающих WIZOR. Описывает КАК работает команда (воркфлоу, роли, форматы), а не только ЧТО строится (продукт — в `.planning/PRD.md`). Написан для агентов в первую очередь.
>
> **Правило чтения (token-efficiency).** Любой агент перед задачей читает: (1) этот charter — целиком один раз за сессию; (2) `.planning/STATUS.md` + `.planning/HANDOFF.md`; (3) свою `.claude/agents/<role>/` папку; (4) phase-spec активной фазы; (5) затронутые контракты. Остальное — JIT, по `MEMORY-INDEX.md`. **Не грузи превентивно.**

---

## 1. Продукт (одним абзацем)

WIZOR — **AI Readiness Platform для РФ**: делает сайт доступным и понятным для ИИ-поиска (ChatGPT/Perplexity/Алиса-Нейро/GigaChat) и замыкает полный цикл **Аудит → Мониторинг → Рекомендации → Авто-имплементация → Верификация**. Главный moat — авто-имплементация правок на стороне сайта (никто на РФ-рынке не делает) + покрытие RU-стека. Модель доступа (v0.2): **read-only-first** — Tier 0 Instant Audit (no-auth) и Manual track (без API) монетизируются сразу, Auto track (API+DPA, авто-применение) — премиум-апгрейд. Полное ТЗ продукта: **`.planning/PRD.md`** (v0.2). Доктрины: differentiation-in-integration-layer, honest-uncertainty, two-tier-proof, trust-ladder, retrieval-first, compliance-by-design (152-ФЗ), evidence-gated-scaling, read-only-first.

---

## 2. 18 проектных решений (decision log харнесса)

| # | Решение | Выбор | ADR |
|---|---------|-------|-----|
| 1 | Субстрат | **Файл-нативный**: агенты = Claude Code Agent tool; память/состояние = git-markdown/JSON; claude-flow/AgentDB — опциональный поздний ускоритель, не обязателен | ADR-0001 |
| 2 | Ростер | **Лёгкое ядро (8) + профильные по требованию (6)** | ADR-0002 |
| 3 | Тиринг моделей | **По типу роли + эскалация/fallback**; Tier-0 без LLM | ADR-0003 |
| 4 | Цикл фазы | **9 шагов** с обязательными пост-аудитом и обновлением памяти | ADR-0004 |
| 5 | Профильные специалисты | **Пишут код своего домена сами** (mode B); в кодинге → Sonnet, Opus только на судение/эскалацию | ADR-0002 |
| 6 | Пост-аудит | **По риск-тиру**: 1 / 3 / 5 линз; стоячий чек-лист инвариантов | ADR-0005 |
| 7 | Память/recall | **Курируемый `MEMORY-INDEX.md` + summary-first**; ротация JOURNAL/STATUS/HANDOFF | ADR-0006 |
| 8 | Роадмап | **~11 зависимостных фаз, read-only-first**; P0+A детально, B/C рамочно | ADR-0007 |
| 9 | Контракты | **Стабы + карта сейчас, api/events/schema — JIT** | ADR-0008 |
| 10 | Git/PR/CI | **Лёгкий PR-на-фазу + тированные CI-гейты**; human-аппрув перенесён на гейт фазы (ADR-0017) | ADR-0009 |
| 11 | Хендоффы | **Компактные структурированные markdown-дельты** (не тяжёлый CloudEvents-JSON) | ADR-0004 |
| 12 | Язык | **Нарратив RU, идентификаторы/код EN** | ADR-0010 |
| 13 | README | Авто-актуализируемый блок статуса (регенерит `memory-curator` на шаге 8) | ADR-0006 |
| 14 | CLAUDE.md | Свой проектный, файл-нативный, без зависимости от глобального ruflo | ADR-0001 |
| 15 | Стек | **Lock из PRD §12** (Python/FastAPI, Next.js, Postgres+pgvector, Celery, Keycloak, Yandex Cloud) | ADR-0011 |
| 16 | Модель доступа | **Three-track: Tier 0 / Manual / Auto** (read-only-first, v0.2) | ADR-0012 |
| 17 | Стартовый дроп | Полный харнесс + все phase-spec'ы + рамочные B/C; скаффолд в `main`, PR с P0 | — |
| 18 | Автономия / human-in-the-loop | **Только гейты фаз**; внутри фазы агенты автономны (мердж/аудит/доп-сессии сами) | ADR-0017 |

---

## 3. Ростер агентов

### 3.1. Ядро (8, persistent — определены всегда, токены тратятся только при вызове)

| Агент | Слой | Модель | Мандат | Когда вызывается |
|---|---|---|---|---|
| `planner` | оркестрация | **Opus** | phase-spec → `PLAN.md`: атомарные задачи, AC, контракты, tier/модель на задачу, нужные специалисты | старт фазы; ре-план при ревизии |
| `architect` | сквозной | **Opus** | ADR, сквозные инварианты, арбитр эскалаций | ADR-моменты, гейты, конфликты |
| `backend-implementer` | реализация | **Sonnet** | Python/FastAPI/SQLAlchemy по контрактам + AC | задачи backend от planner |
| `frontend-implementer` | реализация | **Sonnet** | Next.js/React/shadcn по контрактам + AC | задачи frontend от planner |
| `reviewer` | гейт качества | **Sonnet** | ревью кода (корректность+backend+frontend); security-линза при флаге | после implementer, ≤2 цикла |
| `verifier` | гейт качества | **Haiku** | acceptance-как-тесты + проверка порогов гейта, бинарно | после review |
| `auditor` | гейт качества | **Opus** | адверсариальный пост-аудит, риск-тир (1/3/5 линз), стоячие инварианты | после verify, ОБЯЗАТЕЛЬНО |
| `memory-curator` | сквозной | **Haiku** | единственный писатель состояния/памяти; STATUS/HANDOFF/JOURNAL/MEMORY-INDEX, ротация, архив аудита, авто-README | после audit, ОБЯЗАТЕЛЬНО |

### 3.2. Профильные (6, on-demand — спавнятся ТОЛЬКО когда фаза касается домена; иначе 0 токенов)

| Агент | Модель | Домен |
|---|---|---|
| `geo-domain-expert` | **Opus** | AEO/GEO/SEO, schema/FAQ/citation-левера, веса Readiness Score, honest-forecast, competitive gap |
| `crawler-probe-specialist` | **Sonnet** | Crawlee/Playwright, dual-geo probe, ротация прокси, N≥5+CI, re-crawl, краул конкурентов |
| `llm-router-specialist` | **Opus** | provider-agnostic роутер, RU-default, OSS-fallback, эмбеддинги, uncertainty-статистика |
| `cms-connector-specialist` | **Sonnet** | WordPress plugin/REST, идемпотентность, rollback, IndexNow |
| `compliance-152fz-specialist` | **Opus** | 152-ФЗ, ПДн-резидентность, DPA, append-only audit log, РКН, биллинг-комплаенс |
| `devops-infra-specialist` | **Sonnet** | Yandex Cloud, dual-geo ноды, Docker/CI/CD, секреты (Vault/Lockbox), rate-limit |

**Оркестратор** = founder + главная сессия Claude Code (отдельный агент-координатор не нужен).

### 3.3. Тиринг и эскалация

- **Tier-0 (без LLM):** тривиальные механические правки — делать `Edit`-инструментом напрямую, без агента.
- **Эскалация вверх:** Sonnet-роль помечает задачу `complexity:high` → поднимается до Opus.
- **Fallback вниз:** при перерасходе бюджета — только для лёгких ролей (`reviewer`, `frontend-implementer`, `verifier`, `devops`/`cms`/`crawler` специалисты). **Никогда вниз:** `architect`, `planner`, `auditor`, `compliance-152fz`, `llm-router` судительные задачи, любые security/ПДн-задачи.

### 3.4. Бюджет (cost-budget.yaml; значения — стартовые, founder тюнит)

```
per_task:   soft $0.40  hard $1.50
per_day:    soft $20     hard $50
per_month:  kill_switch $300
stagnation: 30 min без коммита/файла/статуса → авто-стоп
```

---

## 4. Цикл фазы (9 шагов)

1. **Scope** (founder+сессия) — выбрать фазу, прочитать head-summary spec + контракт-стабы, снять open-questions. *[дёшево]*
2. **Plan** (`planner`/Opus) — spec → `PLAN.md` (атомарные задачи, AC, контракты, tier/модель на задачу, специалисты). **Pinned** — без переобдумывания на ходу. *[1 вызов]*
3. **Domain-build** (специалист по требованию) — если фаза касается домена, профильный агент **сам пишет код** своего домена (Sonnet-кодинг, Opus-эскалация).
4. **Implement** (`*-implementer`/Sonnet) — атомарные коммиты, self-audit-чек-лист перед хендоффом.
5. **Review** (`reviewer`/Sonnet) — по чек-листу + контрактам; security-линза при флаге; дельта-находки; **≤2 цикла**, дальше — эскалация к `architect`/founder.
6. **Verify** (`verifier`/Haiku) — acceptance-как-тесты + пороги гейта, бинарно pass/fail.
7. **⭐ Post-audit** (`auditor`/Opus) — ОБЯЗАТЕЛЬНО, риск-тир (§6). Вердикт `PASS`/`PASS-WITH-FIXES`/`BLOCKED`, фиксы в цикле, отчёт в `_session-context/AUDIT-*`.
8. **⭐ Memory-update** (`memory-curator`/Haiku) — ОБЯЗАТЕЛЬНО: STATUS/HANDOFF/JOURNAL (+ротация), patterns/pitfalls в `memory.md`, `MEMORY-INDEX.md`, заполнение гейта, архив аудита, регенерация статус-блока README.
9. **PR + авто-мердж** — внутри фазы PR мерджится автономно (зелёный CI + `reviewer` APPROVE + `auditor` PASS); **человек-аппрув ТОЛЬКО на гейте фазы** (`founder_signature`); squash-merge (ADR-0017).

---

## 5. Роадмап P0–P10 (read-only-first)

Phase 0 + Phase A — детально (ниже). Phase B/C — рамочно (цели + exit-gates из PRD §10–11).

| Фаза | Название | Track | Tier | depends/gated | Контексты | Специалисты | PRD |
|---|---|---|---|---|---|---|---|
| **P0** | Discovery & De-risking (H1–H5) | research | — | параллельно P1–P5 | — | geo, crawler-probe, compliance | §9.0 |
| **P1** | Foundation (repo/CI, multi-tenant, observability, секреты, base app) | infra | 4 | — | iam | devops, compliance | §9.3, FR-6.2 |
| **P2** | Crawler / Аудит (read-only) | read-only | 3 | P1 | crawler, scoring | crawler-probe | EPIC-1/FR-1.1,1.2 |
| **P3** | AI-Readiness Score (детерминированный) | read-only | 3 | P2 | scoring | geo | FR-1.3 |
| **P4** | LLM-router (provider-agnostic, RU-default) | infra | 4 | P1 | llm-router | llm-router | NFR-3 |
| **P5** | Probe-мониторинг (dual-geo, N≥5+CI) | read-only | 3 | P4 | probe, metrics | crawler-probe, llm-router | EPIC-2/FR-2.1–2.4 |
| **P6** | Рекомендации + competitive gap + патчи + honest forecast | read-only | 3 | P3,P5 | recommendations, patches | geo, crawler-probe | EPIC-3/FR-3.1–3.5 |
| **P7** | ⭐ Tier 0 Instant Audit (no-auth PLG) | read-only | 3 | P2–P6 | iam(public), все read-only | geo, devops, frontend | §4.1, §9.1, #17 |
| **P8** | Верификация (Manual proof-loop: re-crawl, deltas, evidence, алерты) | read-only | 3 | P6 | verification, notifications | crawler-probe | EPIC-5/FR-5.1–5.5 |
| **P9** | Auth + биллинг + онбординг + дорожки | infra | 4 | P7,P8 | iam, billing | compliance, devops | EPIC-6/FR-6.1–6.3, §9.4 |
| **P10** | ⭐ Auto track: WP-коннектор + auto-fix + trust-ladder + rollback + DPA | auto | 4 | **gated_by P0**, P9 | autofix, connectors | cms-connector, compliance, geo | EPIC-4/FR-4.1–4.7 |
| → | **A→B gate** | — | — | P0–P10 | — | — | §8 |

**Каждая фаза P1–P10 даёт проверяемый инкремент и проходит полный 9-шаговый цикл со своим гейтом.** Ценность монетизируется уже на P7 (Tier 0) и P9 (Manual track платно), Auto-fix (P10) — апгрейд.

---

## 6. Пост-аудит: риск-тир + стоячие инварианты

**Глубина по tier фазы (см. колонку Tier роадмапа):**
- **Tier 1–2** → 1 адверсариальная линза (1 Opus-проход).
- **Tier 3** → 3 линзы: корректность · security · compliance.
- **Tier 4** (архитектура/биллинг/auto-fix-на-prod/ПДн) → полный 5-линзовый swarm: корректность · security · compliance · тесты · архитектура.

**Стоячий чек-лист инвариантов (проверяется в КАЖДОМ аудите):**
1. **Read-only-граница:** Tier 0 / Manual track — ноль write/API-вызовов; DPA/API — гейт ТОЛЬКО Auto track, не входа в продукт. *(FR-4.7, §4.1)*
2. **Honest forecast:** нигде нет гарантированного Visibility-%; всегда диапазон+доверие; Readiness-проекция детерминирована. *(FR-3.5)*
3. **Auto-fix safety:** идемпотентность + обратимость + append-only audit log; DPA акцептован ДО любой авто-правки. *(FR-4.1/4.4/4.5/4.6)*
4. **Probe-гео:** ни один probe к ChatGPT/Perplexity не с РФ-IP. *(FR-2.2, NFR-2)*
5. **llms.txt** НЕ весит в citation/Readiness Score. *(FR-1.3)*
6. **ПДн-резидентность:** ПД клиентов хостятся/обрабатываются в РФ (Yandex Cloud); контент клиента по умолчанию — RU-модели. *(NFR-1/3)*
7. **Uncertainty:** улучшение Visibility заявляется только вне полосы шума (N≥5+CI). *(FR-2.3/5.2)*
8. **Multi-tenant изоляция** (`tenant_id`); нет cross-tenant утечки. *(FR-6.2)*
9. **Секреты** никогда не в коде/коммитах.
10. **FAQ (видимый контент)** никогда не авто-применяется — только review. *(FR-4.2/4.3)*

Формат отчёта: `_session-context/AUDIT-YYYY-MM-DD-<phase>/AUDIT-REPORT.md` (вердикт + таблица диспозиции находок: fixed-in-loop / deferred-to-AC / blocked) + посекционные файлы по линзам. После merge → `_session-context/archive/`.

---

## 7. Bounded contexts (карта; 13 шт.; стабы сейчас, api/events/schema JIT)

| Контекст | Назначение | Track | Зависит от |
|---|---|---|---|
| `iam` | auth (Keycloak/OIDC), multi-tenancy (`tenant_id`), entitlements дорожек (Tier0/Manual/Auto) | infra | — |
| `crawler` | краул сайта + конкурентов + re-crawl (read-only) | read-only | — |
| `scoring` | AI-Readiness Score (детерминированный) | read-only | crawler |
| `probe` | LLM-probe мониторинг (dual-geo, N≥5+CI) | read-only | llm-router |
| `metrics` | Visibility/Coverage/SoV/Citation/Stability, uncertainty | read-only | probe |
| `recommendations` | прио-фиксы, competitive gap, honest forecast, FAQ-gen | read-only | scoring, metrics |
| `patches` | генерация copy-paste артефактов (read-only) | read-only | recommendations |
| `connectors` | применение патчей через CMS (WP) | auto | patches |
| `autofix` | trust-ladder, audit-log, rollback, DPA-оркестрация | auto | connectors |
| `verification` | readiness/visibility-delta, evidence, re-crawl-verify, алерты | read-only | scoring, metrics |
| `llm-router` | provider-agnostic gateway, RU-default, OSS-fallback | infra | — |
| `billing` | ЮKassa, тарифы, trial, entitlements дорожек | infra | iam |
| `notifications` | email/Telegram/webhook алерты | infra | — |

Compliance (152-ФЗ) — **сквозной инвариант**, не контекст (см. §6, инварианты 1/3/6).

---

## 8. Форматы файлов (ОБЯЗАТЕЛЬНЫ к соблюдению всеми агентами)

### 8.1. Агент: `.claude/agents/<role>/` (LEAN — суммарно ~10–12 KB/агент, против ~40–50 KB у ORIION)

- **`profile.md`** (~0.5 KB): frontmatter `name, layer, model, kind: persistent|on-demand` + мандат (1–2 предл.), triggers, owns (namespace/файлы памяти), escalates_to.
- **`system-prompt.md`** (**≤4 KB** — главная token-экономия): секции — Identity · Inputs · Outputs · Invariants (ссылка на §6 charter, не переписывать) · Delegation · «What you do NOT do» · Failure modes. Ссылайся на charter/conventions, **не дублируй**.
- **`workflows.md`** (≤3 KB): 1–3 канонических плейбука (trigger → steps → output → handoff).
- **`memory.md`** (≤1.5 KB): owned namespace/файлы, MUST-persist, MUST-NOT, retrieval-queries, pruning.
- **`handoff-templates.md`** (≤1.5 KB): inbound/outbound компактные блоки (формат §8.6).
- **`tools-allowlist.md`** (≤1 KB): allowed-инструменты + denied (least-privilege).
- **`checklists/`** (опц., ≤1 KB/файл): self-audit по типам задач.

### 8.2. Phase-spec: `.planning/roadmap/PNN-<slug>.md`

```
---
phase: P2
slug: crawler-audit
title: ...
status: planned        # planned|active|done|deferred
tier: 3
track: read-only       # read-only|auto|infra|research
depends_on: [P1]
gated_by: []           # напр. [P0] для P10
contracts: [crawler, scoring]
specialists: [crawler-probe-specialist]
prd_refs: [EPIC-1/FR-1.1, FR-1.2]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): ... -->
## Goal
## In scope
## Out of scope
## Functional requirements   (← цитировать PRD FR + AC)
## Acceptance criteria
## Contracts touched
## Exit-gate                  (измеримые пороги)
## Decomposition hints for planner
```

### 8.3. ADR: `.planning/decisions/ADR-NNNN-<slug>.md`

```
---
id: ADR-0001
title: ...
status: accepted     # proposed|accepted|superseded
date: 2026-06-23
supersedes: []
---
## Context
## Decision
## Consequences
## Alternatives considered
```

### 8.4. Контракт-стаб: `.planning/contracts/<ctx>/README.md`

```
# Context: <name>
**Purpose:** ...
**Owns (data):** ...
**Track:** read-only | auto | infra
**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании фазы]
**Emits (events):** [STUB — events.yaml JIT]
**Depends on:** [контексты]
**Schema:** [STUB — schema.sql JIT]
**Invariants:** [ссылки на §6]
```

Плюс `.planning/contracts/README.md` = карта всех контекстов (таблица §7).

### 8.5. Gate: `.planning/gates/<id>.md` (frontmatter валидируется `gates/_schema/gate.schema.json`)

```
---
gate: P0-to-heavy-autofix
status: pending        # pending|passed|blocked|waived
opened_at: 2026-06-23
closed_at: null
founder_signature: null
hard_thresholds:
  H1_api_willingness: { target: proven, actual: null, passed: null, evidence_url: null }
deliverables: [{ id: D1, name: ..., status: pending }]
adr_delta: { created: [], revised: [] }
risks_delta: { opened: [], closed: [] }
---
## Rationale
## Checklist
```

### 8.6. Хендофф (компактный markdown-блок, НЕ CloudEvents-JSON)

```
### HANDOFF <from> → <to> · <phase> · <ISO-ts>
- task: <одна строка>
- did: <ключевое>
- artifacts: [файлы]
- contracts_touched: [...]
- self_audit: pass|fail  (+ ссылка на checklist)
- next: <следующее действие>
- escalate: none | <причина+вопрос>
```

---

## 9. Конвенции

- **Язык:** нарратив/комментарии — RU; идентификаторы, имена файлов/папок, enum'ы, типы событий, поля схем, код — EN.
- **Naming:** фазы `PNN-slug`; ADR `ADR-NNNN-slug`; ветки `phase/PNN-slug`; коммиты — Conventional Commits, в футере `Refs: PNN, ADR-NNNN`.
- **Token-budgets (ориентиры контекста на задачу):** простой фикс 5–10 KB; эндпоинт 10–20 KB; фаза 30–60 KB; при приближении к 120 KB — делегируй в суб-агента или handoff+новая сессия.
- **Стек:** строго PRD §12 (Python 3.12/FastAPI/Pydantic v2/SQLAlchemy; Postgres 16+pgvector; Redis; Celery; Keycloak; Next.js 15/React 19/shadcn; Yandex Cloud + Hetzner/Selectel для зарубежного probe).
- **DoD задачи:** AC выполнены · CI зелёный · self-audit пройден · контракты соблюдены · память обновлена · хендофф записан.

---

## 10. Память и recall

- **`MEMORY-INDEX.md`** (корень `.planning/`): таблица `| tag | topic | pointer (file:section) | gist (1 строка) | updated |`. Агент читает индекс → грузит полный текст только при попадании.
- **Head-summary:** у каждого дока >2 KB — блок `<!-- HEAD-SUMMARY (≤500т): ... -->` в начале. Агент читает summary первым.
- **Ротация:** `JOURNAL.md` >300 строк → `_session-context/archive/JOURNAL-YYYY-Qn.md`; `STATUS.md` — только rolling-состояние (история фаз → `PHASE-HISTORY.md`); `HANDOFF.md` ≤2 KB снапшот.
- **`memory-curator`** — единственный писатель состояния/памяти. MUST-NOT: секреты, полный код, чужой контент (только ссылки).
- **claude-flow/AgentDB** — опциональный семантический индекс поверх тех же файлов; включается, когда история перерастёт grep (документируется, но в дефолте выключен).

---

## 11. Автономия и доп-сессии (ADR-0017)

**Human-in-the-loop = только гейт фазы.** Единственная штатная точка ревью человеком — exit-гейт (`gates/*.md`, `founder_signature`). Внутри фазы агенты планируют, реализуют, ревьюят, верифицируют, аудируют и **мерджат PR автономно** (зелёный CI + `reviewer` APPROVE + `auditor` PASS). Per-PR human-аппрув упразднён.

**Автономные доп-сессии.** Оркестратор и суб-агенты могут запускать доп. сессии Claude Code: (a) Agent tool (свежий контекст) — параллельные независимые задачи; (b) headless `claude -p` — полностью независимая сессия; (c) управление контекстом — при ~120 KB: handoff → свежая сессия.

**Guardrails:** глубина спавна ≤ 2; одновременных сессий ≤ 8; cost kill-switch ($300/мес) + stagnation-kill (30 мин); каждая единица пишет handoff; `memory-curator` — единственный писатель состояния; граница автономии = scope активной фазы.

**Эскалация — исключение, не ревью.** Рутинное «проверь работу» → `reviewer`/`auditor`. К founder — только реальный блокер или его территория (юр/деньги/бренд/стратегия), асинхронно (флаг в HANDOFF).

**Граница автономии.** Необратимые ВНЕШНИЕ действия (правки на реальном клиентском prod, живые списания, подпись DPA, внешние коммуникации) НЕ покрыты dev-автономией — это product-runtime, управляется trust-ladder + DPA (ADR-0015) и opt-in пользователя.

---

*Charter v1.1 · 2026-06-23 · источник истины для всех build-агентов WIZOR. Изменения — только через ADR. v1.1: +ADR-0017 (автономия; human-чекпоинт только на гейтах фаз).*
