---
id: ADR-0008
title: contracts-stubs-plus-jit
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Контракты bounded context'ов создаются как стабы (карта + purpose + invariants) сразу; api/events/schema-детали заполняются JIT при планировании соответствующей фазы. -->

## Context

WIZOR содержит 13 bounded contexts. Детально специфицировать все контракты (api.yaml, events.yaml, schema.sql) на старте — дорого и преждевременно: большинство контекстов (autofix, connectors, billing) реализуются в поздних фазах, и ранняя детализация обречена на устаревание. При этом карта контекстов и инварианты зависимостей нужны с первого дня.

## Decision

Каждый bounded context получает **стаб-контракт** в `.planning/contracts/<ctx>/README.md` при запуске харнесса (формат Charter §8.4): Purpose · Owns · Track · Exposes (STUB) · Emits (STUB) · Depends on · Schema (STUB) · Invariants. **api.yaml, events.yaml, schema.sql** заполняются **JIT** — только когда planner планирует фазу, касающуюся данного контекста. `.planning/contracts/README.md` содержит карту всех 13 контекстов (§7 Charter).

## Consequences

- Карта зависимостей и инварианты доступны всем агентам с дня 1 без переспецификации.
- Нет «мёртвых» детализированных контрактов, которые никогда не будут реализованы.
- JIT-детализация происходит в правильный момент — когда planner имеет полный контекст фазы.
- Компромисс: агент, работающий с контекстом впервые, получит STUB вместо полного контракта — это сигнал написать его сейчас.
- Implementer НЕ начинает реализацию без заполненного api.yaml для своего контекста.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Полные контракты сразу | Нет пробелов | 70% устареют до реализации | Overengineering на старте |
| Нет контрактов вообще | Максимальная скорость | Нет карты зависимостей; инвариант-нарушения невидимы | Нарушает bounded-context принципы |
| Только schema.sql | Быстро | API и события не специфицированы | Недостаточно для multi-context координации |

## Links

- Charter: `BUILD-CHARTER.md §2 (#9), §7, §8.4`
- PRD: —
- Related ADRs: ADR-0001 (substrate), ADR-0011 (stack lock)
