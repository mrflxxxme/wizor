<!-- HEAD-SUMMARY (≤500т): Индекс всех ADR WIZOR. 28 принятых решений: 12 workflow-харнесс (ADR-0001–0012) + 4 product-baseline (ADR-0013–0016) + ADR-0017 (автономия) + ADR-0018 (тесты+live-gold) + ADR-0019 (PR открыт сразу) + ADR-0020 (исполняемый слой) + ADR-0021 (автономный runner — порт ORIION ADR-037) + ADR-0022–0028 (grill-интервью 2026-07-07: live-gold классы, дефолты P9/P10, prompt-set gen, async Tier-0, frontend UI-SPEC, P6.5 prod-деплой, golden e2e DoD). ADR-0001–0018 — 2026-06-23, ADR-0019 — 2026-06-24, ADR-0020/0021 — 2026-07-03, ADR-0022–0028 — 2026-07-07. -->

# ADR Index — WIZOR

Все изменения архитектуры и харнесса — только через новый ADR. Формат файлов: `ADR-template.md`.

| ID | Slug | Название (RU) | Статус | Дата |
|---|---|---|---|---|
| ADR-0001 | file-native-substrate | Файл-нативный субстрат (claude-flow опционально) | accepted | 2026-06-23 |
| ADR-0002 | lean-roster-8-core-plus-6-specialists | Ростер: 8 ядро + 6 профильных on-demand, mode B | accepted | 2026-06-23 |
| ADR-0003 | model-tiering-by-role | Тиринг моделей по роли + эскалация/fallback, Tier-0 без LLM | accepted | 2026-06-23 |
| ADR-0004 | nine-step-phase-loop | 9-шаговый цикл фазы + компактные markdown-хендоффы | accepted | 2026-06-23 |
| ADR-0005 | risk-tiered-post-audit | Пост-аудит по риск-тиру: 1/3/5 линз + 10 стоячих инвариантов | accepted | 2026-06-23 |
| ADR-0006 | file-native-memory | Файл-нативная память: MEMORY-INDEX + summary-first + ротация + auto-README | accepted | 2026-06-23 |
| ADR-0007 | read-only-first-roadmap | Роадмап P0–P10 read-only-first; авто-применение (P10) gated by P0 | accepted | 2026-06-23 |
| ADR-0008 | contracts-stubs-plus-jit | Стабы контрактов сразу, api/events/schema — JIT при планировании фазы | accepted | 2026-06-23 |
| ADR-0009 | lightweight-pr-per-phase-tiered-ci | Лёгкий PR на фазу + тированные CI-гейты (human-аппрув перенесён на гейт фазы — amended by ADR-0017) | accepted | 2026-06-23 |
| ADR-0010 | language-ru-narrative-en-identifiers | Язык: нарратив RU, идентификаторы/код EN | accepted | 2026-06-23 |
| ADR-0011 | stack-lock | Стек зафиксирован по PRD §12 (boring tech) | accepted | 2026-06-23 |
| ADR-0012 | three-track-access-model | Three-track: Tier 0 / Manual / Auto; DPA/API — gate только Auto | accepted | 2026-06-23 |
| ADR-0013 | multi-tenancy-tenant-id-day-1 | Multi-tenancy tenant_id с дня 1; изоляция = стоячий инвариант | accepted | 2026-06-23 |
| ADR-0014 | dual-geo-probe-no-ru-ip | Dual-geo probe: RU-ноды для RU-моделей, зарубежные ноды для ChatGPT/Perplexity | accepted | 2026-06-23 |
| ADR-0015 | trust-ladder-and-dpa | Trust ladder: approval-gate→opt-in auto; DPA обязателен; rollback; audit-log | accepted | 2026-06-23 |
| ADR-0016 | llms-txt-not-citation-weighted | llms.txt не в citation-весе/Score; honest-uncertainty: N≥5+CI, нет гарантированных Visibility-% | accepted | 2026-06-23 |
| ADR-0017 | phase-gate-only-autonomy | Человек-ревью только на гейтах фаз; внутри фазы полная автономия (мердж/аудит/доп-сессии сами); amends ADR-0009 | accepted | 2026-06-23 |
| ADR-0018 | mandatory-tests-and-live-gold-before-pr | Обязательные self-run тесты + live-gold (где возможно) перед PR; evidence в гейт; amends ADR-0017 | accepted | 2026-06-23 |
| ADR-0019 | open-pr-not-draft | PR создаётся сразу открытым (ready-for-review), не draft; чеки/ревью немедленно; founder видит итог; дополняет ADR-0017, amends ADR-0009 | accepted | 2026-06-24 |
| ADR-0020 | executable-harness-layer | Исполняемый слой: slash-команды + SessionStart-хук + permission-allowlist + role-loader (спавн из `<role>/`-доков без дублей); amends ADR-0001/0002 | accepted | 2026-07-03 |
| ADR-0021 | autonomous-multiphase-runner | Автономный runner: строгий гейт-стек = merge-authority (порт ORIION ADR-037; tripwire/evidence/escalation/judge/heal); amends ADR-0017/0018/0009 | accepted | 2026-07-03 |
| ADR-0022 | live-gold-resource-policy-and-ac-classification | Классификация AC на mock-verifiable/live-only; live-only = явные gate-blocker'ы; founder даёт live-набор до P7; amends ADR-0018 | accepted | 2026-07-07 |
| ADR-0023 | p9-p10-product-defaults | Дефолты: trial 14/30 дн; trust-ladder approval-gate + per-type opt-in сразу; цена Manual = Auto; revisit_after P0/данные | accepted | 2026-07-07 |
| ADR-0024 | prompt-set-generation | Авто-ген N≈10 промптов из crawl через LLM-router (RU-default), версионируются; модуль в P6, редактор в P9 | accepted | 2026-07-07 |
| ADR-0025 | async-tier0-audit | Tier-0 async job-модель: POST→job_id мгновенно; результат поэтапно (Score+патчи ≤90с, visibility+gap ≤5мин) | accepted | 2026-07-07 |
| ADR-0026 | frontend-ui-spec-and-per-phase-ac | UI-SPEC (инвентарь экранов) + frontend-scope/AC в каждую фазу P6–P10 | accepted | 2026-07-07 |
| ADR-0027 | production-deploy-phase | Отдельная инфра-фаза P6.5 (YC IaC + домен + TLS + CD + observability); параллельно P6; P7 зависит | accepted | 2026-07-07 |
| ADR-0028 | golden-e2e-mvp-acceptance | Golden e2e-сценарий = DoD MVP в A→B gate + track-smoke'и после P7/P9/P10 | accepted | 2026-07-07 |

## Связи с Charter §2 (decision log)

| Charter # | Решение | ADR |
|---|---|---|
| 1 | Субстрат | ADR-0001 |
| 2 | Ростер | ADR-0002 |
| 3 | Тиринг моделей | ADR-0003 |
| 4 | Цикл фазы | ADR-0004 |
| 5 | Профильные (mode B) | ADR-0002 |
| 6 | Пост-аудит | ADR-0005 |
| 7 | Память/recall | ADR-0006 |
| 8 | Роадмап | ADR-0007 |
| 9 | Контракты | ADR-0008 |
| 10 | Git/PR/CI | ADR-0009 |
| 11 | Хендоффы | ADR-0004 |
| 12 | Язык | ADR-0010 |
| 13 | README авто | ADR-0006 |
| 14 | CLAUDE.md | ADR-0001 |
| 15 | Стек | ADR-0011 |
| 16 | Модель доступа | ADR-0012 |
| 18 | Автономия / human-in-the-loop (гейт-only) | ADR-0017 |
| 19 | Тесты + live-gold перед PR | ADR-0018 |
| 20 | Состояние PR (open, не draft) | ADR-0019 |
| 21 | Исполняемый слой (команды/хуки/role-loader) | ADR-0020 |
| 22 | Автономный многофазный runner (порт ADR-037) | ADR-0021 |
| 23 | Live-gold политика (mock/live классы) | ADR-0022 |
| 24 | Дефолты P9/P10 | ADR-0023 |
| 25 | Prompt-set generation | ADR-0024 |
| 26 | Tier-0 UX (async) | ADR-0025 |
| 27 | Frontend (UI-SPEC + per-phase AC) | ADR-0026 |
| 28 | Prod-деплой (P6.5) | ADR-0027 |
| 29 | Definition of Done MVP (golden e2e) | ADR-0028 |
| Product-1 | Multi-tenancy | ADR-0013 |
| Product-2 | Dual-geo probe | ADR-0014 |
| Product-3 | Trust ladder + DPA | ADR-0015 |
| Product-4 | llms.txt + honest-uncertainty | ADR-0016 |
