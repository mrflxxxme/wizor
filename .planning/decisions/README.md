<!-- HEAD-SUMMARY (≤500т): Индекс всех ADR WIZOR. 17 принятых решений: 12 workflow-харнесс (ADR-0001–0012) + 4 product-baseline (ADR-0013–0016) + ADR-0017 (автономия / гейт-only). Все accepted, 2026-06-23. -->

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
| Product-1 | Multi-tenancy | ADR-0013 |
| Product-2 | Dual-geo probe | ADR-0014 |
| Product-3 | Trust ladder + DPA | ADR-0015 |
| Product-4 | llms.txt + honest-uncertainty | ADR-0016 |
