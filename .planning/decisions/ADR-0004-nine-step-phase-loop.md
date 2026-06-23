---
id: ADR-0004
title: nine-step-phase-loop
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Каждая фаза проходит 9 шагов: Scope→Plan→Domain-build→Implement→Review→Verify→Post-audit→Memory-update→PR; хендоффы — компактные markdown-блоки. -->

## Context

WIZOR разрабатывается ИИ-командой без постоянного human-надзора между шагами. Нужен явный, верифицируемый цикл фазы, гарантирующий: (а) качество не деградирует к концу фазы без ревью, (б) состояние не теряется при смене сессии, (в) аудит проводится обязательно, а не по желанию. Лёгкие форматы хендоффов позволяют передавать контекст без раздувания токен-окна.

## Decision

Все фазы P1–P10 проходят **9 обязательных шагов**:
1. Scope (founder + сессия) — head-summary + open-questions.
2. Plan (planner/Opus) → `PLAN.md` (pinned, не пересматривается на ходу).
3. Domain-build (профильный специалист, если фаза задевает домен).
4. Implement (*-implementer/Sonnet) — атомарные коммиты + self-audit checklist.
5. Review (reviewer/Sonnet) — по чек-листу + контрактам; ≤2 цикла, дальше escalate.
6. Verify (verifier/Haiku) — acceptance-тесты, бинарно pass/fail.
7. **⭐ Post-audit** (auditor/Opus) — ОБЯЗАТЕЛЬНО; риск-тир (§6 Charter); вердикт PASS/PASS-WITH-FIXES/BLOCKED.
8. **⭐ Memory-update** (memory-curator/Haiku) — ОБЯЗАТЕЛЬНО; STATUS/HANDOFF/JOURNAL + ротация + MEMORY-INDEX + auto-README.
9. PR + аппрув (founder) — tier-based; squash-merge.

**Хендоффы** между агентами — компактные структурированные markdown-блоки (Charter §8.6), не CloudEvents-JSON.

## Consequences

- Пост-аудит и обновление памяти не могут быть пропущены; это архитектурный инвариант, а не «если успеем».
- PLAN.md фиксируется на шаге 2 и не переписывается на ходу — устраняет drift и «творческий рефакторинг» в ходе реализации.
- ≤2 цикла review — жёсткий предел; дальше эскалация к architect/founder предотвращает бесконечные петли.
- Компромисс: 9 шагов тяжелее 3-шагового цикла; оправдано для Tier 3–4 фаз; Tier 1–2 могут collapse шаги 3+5 без domain-build.
- Хендоффы-markdown компактнее JSON, но менее машино-парсируемы; достаточно при текущем масштабе.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Свободный цикл без фиксированных шагов | Гибкость | Аудит пропускается; состояние теряется | Нет гарантий качества |
| CloudEvents JSON-хендоффы | Машиночитаемость | ~5× тяжелее; избыточно для 8-агентной команды | Заменены markdown-блоками |
| Audit по желанию | Экономия | Упущенные инварианты invariants-нарушения | Инварианты Charter §6 требуют обязательного аудита |

## Links

- Charter: `BUILD-CHARTER.md §4, §8.6`
- PRD: —
- Related ADRs: ADR-0005 (post-audit), ADR-0006 (memory), ADR-0009 (PR/CI)
