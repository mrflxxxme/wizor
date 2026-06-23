---
id: ADR-0003
title: model-tiering-by-role
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Три тира модели (Tier-0 без LLM / Haiku / Sonnet / Opus) назначены по типу роли; эскалация вверх по complexity:high; жёсткий запрет fallback для security/compliance/architect. -->

## Context

Бюджет (soft $0.40/задача, kill $300/мес) требует дифференцированного расхода токенов по сложности. При этом ошибки в security/compliance/architecture несравнимо дороже экономии на модели. Нужна схема, где цена ошибки и цена токена вместе определяют выбор.

## Decision

Роли получают **роль-фиксированный дефолт** с правилами эскалации:
- **Tier-0 (без LLM):** тривиальные механические правки → Edit-инструмент напрямую.
- **Haiku:** verifier (бинарный pass/fail тест), memory-curator (структурированный write).
- **Sonnet:** backend-implementer, frontend-implementer, reviewer, crawler-probe-specialist, cms-connector-specialist, devops-infra-specialist (кодинг-задачи).
- **Opus:** planner (spec→plan), architect (ADR/арбитраж), auditor (адверсариальный аудит), geo-domain-expert, llm-router-specialist, compliance-152fz-specialist (суждение/риски).

**Эскалация вверх:** любая Sonnet-роль помечает задачу `complexity:high` → поднимается до Opus. **Fallback вниз разрешён** только для лёгких ролей (reviewer, frontend-implementer, verifier, devops/cms/crawler специалисты) при перерасходе бюджета. **Никогда вниз:** architect, planner, auditor, compliance-152fz, llm-router для суждения, любые security/ПДн-задачи.

## Consequences

- Предсказуемый cost-profile; Opus вызывается только там, где суждение критично.
- Явное правило «никогда вниз» защищает от экономии ценой безопасности.
- cost-budget.yaml содержит soft/hard/kill-switch лимиты; stagnation-стоп через 30 минут без артефакта.
- Компромисс: planner должен правильно помечать complexity; ложный complexity:high = лишний Opus-вызов.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Opus для всех | Максимальное качество | $$$; kill switch через неделю | Нецелесообразно |
| Единый Sonnet | Баланс цена/качество | Слабое суждение в audit/compliance | Риск в ADR/security задачах |
| Динамический тиринг по токенам промпта | Адаптивно | Непредсказуемо; сложно отлаживать | Роль-фиксированный дефолт проще и аудируемей |

## Links

- Charter: `BUILD-CHARTER.md §3.3, §3.4`
- PRD: —
- Related ADRs: ADR-0002 (roster), ADR-0005 (post-audit)
