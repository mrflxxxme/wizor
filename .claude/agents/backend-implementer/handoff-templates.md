# backend-implementer — handoff templates

## Outbound: backend-implementer → reviewer

```
### HANDOFF backend-implementer → reviewer · <phase> · <ISO-ts>
- task: <task-id> реализован
- did: FastAPI route + Pydantic schema + SQLAlchemy model + тесты
- artifacts: [src/<ctx>/<files>, tests/<ctx>/<files>]
- contracts_touched: [<ctx>]
- self_audit: pass (checklists/self-audit.md)
- next: reviewer проверяет по чек-листу + контрактам
- escalate: none | complexity:high — рекомендую architect-ревью на <конкретный раздел>
```

## Outbound: backend-implementer → architect (эскалация)

```
### HANDOFF backend-implementer → architect · <phase> · <ISO-ts>
- task: complexity:high — нужно architectural решение
- did: дошёл до точки неоднозначности в контракте
- artifacts: [.planning/contracts/<ctx>/README.md]
- contracts_touched: [<ctx>]
- self_audit: n/a (blocked)
- next: architect создаёт ADR; implementer продолжает после
- escalate: <конкретный вопрос об архитектуре>
```

## Inbound: от planner / от reviewer (fix)

```
### HANDOFF planner → backend-implementer · <phase> · <ISO-ts>
- task: <task-id> — <описание>
- did: создал PLAN.md с задачей
- artifacts: [.planning/PLAN.md, .planning/contracts/<ctx>/README.md]
- contracts_touched: [<ctx>]
- self_audit: n/a
- next: backend-implementer реализует, пишет тесты, self-audit
- escalate: none
```
