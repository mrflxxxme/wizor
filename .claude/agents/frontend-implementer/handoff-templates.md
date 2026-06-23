# frontend-implementer — handoff templates

## Outbound: frontend-implementer → reviewer

```
### HANDOFF frontend-implementer → reviewer · <phase> · <ISO-ts>
- task: <task-id> реализован
- did: Next.js page + React компоненты + shadcn/ui + API-интеграция
- artifacts: [src/<ctx>/<files>, tests/<ctx>/<files>]
- contracts_touched: [<ctx>]
- self_audit: pass (checklists/self-audit.md)
- next: reviewer проверяет по чек-листу
- escalate: none | tier0_public: true (если задача P7 Tier 0)
```

## Outbound: frontend-implementer → architect (эскалация)

```
### HANDOFF frontend-implementer → architect · <phase> · <ISO-ts>
- task: complexity:high — нужно решение
- did: дошёл до неоднозначности в UX/API-контракте
- artifacts: [.planning/contracts/<ctx>/README.md]
- contracts_touched: [<ctx>]
- self_audit: n/a (blocked)
- next: architect/founder принимает решение
- escalate: <конкретный вопрос>
```

## Inbound: от planner / от reviewer (fix)

```
### HANDOFF planner → frontend-implementer · <phase> · <ISO-ts>
- task: <task-id> — <описание>
- did: создал PLAN.md с задачей
- artifacts: [.planning/PLAN.md, .planning/contracts/<ctx>/README.md]
- contracts_touched: [<ctx>]
- self_audit: n/a
- next: frontend-implementer реализует, пишет тесты, self-audit
- escalate: none
```
