---
id: ADR-0009
title: lightweight-pr-per-phase-tiered-ci
status: accepted
date: 2026-06-23
supersedes: []
amended_by: [ADR-0017]
---
<!-- HEAD-SUMMARY (≤500т): Один PR на фазу; CI-гейты пропорциональны tier фазы; founder — единственный человек-апрувер на tier 3+ (⚠ AMENDED by ADR-0017: human-аппрув перенесён на гейт фазы, внутри фазы авто-мердж); tier 1–2 авто-мердж на зелёном CI. -->

> ⚠️ **Amended by [ADR-0017]** (2026-06-23): человеческий аппрув перенесён с per-PR tier 3+ на **гейт фазы**; внутри фазы PR авто-мерджятся (CI + `reviewer` + `auditor` PASS). Текст ниже — исходное решение; действующая модель — ADR-0017.

## Context

Команда = founder + ИИ-агенты; нет команды ревьюеров. PR-процесс должен обеспечить точку человеческого контроля на значимых изменениях, не блокируя при этом скорость на рутинных. Тяжёлый CI на каждом коммите при small-team = расточительство; слишком лёгкий = пропущенные инварианты.

## Decision

**Один PR на фазу** (ветка `phase/PNN-slug`); squash-merge после прохождения gate. CI-гейты пропорциональны tier фазы:
- **Tier 1–2:** линт + unit-тесты → зелёный CI → **авто-мердж** (без человека).
- **Tier 3:** + интеграционные тесты + schema-валидация → **требует approve founder'а**.
- **Tier 4:** + security scan + compliance check + полный e2e → **требует approve founder'а + вердикт PASS auditor'а** из шага 7.

**Founder — единственный human-approver** на tier 3+. Коммиты следуют Conventional Commits с футером `Refs: PNN, ADR-NNNN`.

## Consequences

- Tier 1–2 фазы (чистые refactor/docs/infra-setup) не создают bottleneck у founder'а.
- Tier 4 (auto-fix на prod, ПДн, биллинг) получает максимальную точку контроля: аудит + founder.
- Ветка `phase/PNN-slug` чётко соответствует phase-spec; история читаема.
- Компромисс: один PR на фазу = большой diff; атомарные коммиты внутри ветки облегчают ревью.
- GitLab CI (РФ) / GitHub Actions — оба поддерживаются (PRD §12 infra).

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| PR на каждый коммит | Максимальная гранулярность | Founder перегружен approve | Нецелесообразно при 9-шаговом цикле |
| Нет PR, direct push | Скорость | Нет точки контроля на тяжёлых фазах | Неприемлемо для auto-fix/ПДн фаз |
| Полный CI на каждом push | Полное покрытие | Дорого и медленно на Tier 1 | Tier-based подход балансирует |

## Links

- Charter: `BUILD-CHARTER.md §2 (#10), §4 (шаг 9), §9`
- PRD: `PRD.md §12 (DevOps)`
- Related ADRs: ADR-0004 (phase loop), ADR-0005 (post-audit)
