# architect — handoff templates

## Outbound: architect → эскалирующий агент (ADR создан)

```
### HANDOFF architect → <role> · <phase> · <ISO-ts>
- task: архитектурное решение принято
- did: создал ADR-<NNNN>-<slug>.md
- artifacts: [.planning/decisions/ADR-<NNNN>-<slug>.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: <role> продолжает работу с учётом ADR-<NNNN>
- escalate: none
```

## Outbound: architect → founder (gate tier 4 / BLOCKED)

```
### HANDOFF architect → founder · <phase> · <ISO-ts>
- task: требуется founder sign-off
- did: проверил gate / получил BLOCKED эскалацию
- artifacts: [.planning/gates/<id>.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: founder подписывает gate или принимает решение по BLOCKED
- escalate: <причина + конкретный вопрос>
```

## Inbound: от агента (эскалация)

```
### HANDOFF <role> → architect · <phase> · <ISO-ts>
- task: требуется архитектурное решение
- did: <что сделал агент до эскалации>
- artifacts: [<файлы контекста>]
- contracts_touched: [<ctx>]
- self_audit: pass|fail
- next: architect создаёт ADR
- escalate: <конкретный вопрос>
```
