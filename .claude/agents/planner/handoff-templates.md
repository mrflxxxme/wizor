# planner — handoff templates

## Outbound: planner → implementer / specialist

```
### HANDOFF planner → <role> · <phase> · <ISO-ts>
- task: <task-id> из PLAN.md — <одна строка описания>
- did: создал PLAN.md; декомпозировал на <N> атомарных задач
- artifacts: [.planning/PLAN.md]
- contracts_touched: [<ctx1>, <ctx2>]
- self_audit: pass
- next: реализовать task <task-id>, AC: <список AC>
- escalate: none
```

## Outbound: planner → architect (эскалация)

```
### HANDOFF planner → architect · <phase> · <ISO-ts>
- task: требуется архитектурное решение перед созданием PLAN.md
- did: обнаружил конфликт / неоднозначность контракта
- artifacts: [.planning/roadmap/<phase-spec>.md]
- contracts_touched: [<ctx>]
- self_audit: n/a (blocked)
- next: architect создаёт ADR; planner финализирует PLAN.md после
- escalate: <конкретный вопрос в 1–2 строки>
```

## Inbound: от founder (старт фазы)

```
### HANDOFF founder → planner · <phase> · <ISO-ts>
- task: спланировать фазу <PNN>
- did: выбрал фазу из роадмапа
- artifacts: [.planning/roadmap/<PNN>-<slug>.md]
- contracts_touched: [<ctx>]
- self_audit: n/a
- next: planner читает spec + создаёт PLAN.md
- escalate: none
```
