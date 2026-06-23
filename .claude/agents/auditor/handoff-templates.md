# auditor — handoff templates

## Outbound: auditor → memory-curator (PASS / PASS-WITH-FIXES)

```
### HANDOFF auditor → memory-curator · <phase> · <ISO-ts>
- task: post-audit завершён — <PASS | PASS-WITH-FIXES>
- did: <N>-линзовый аудит (tier <T>); проверил 10 инвариантов charter §6
- artifacts: [_session-context/AUDIT-<date>-<phase>/AUDIT-REPORT.md]
- contracts_touched: [<ctx>]
- self_audit: pass (checklists/invariant-checklist.md)
- next: memory-curator выполняет шаг 8 цикла (все 8 обновлений)
- escalate: none | deferred: [<finding-id> → AC <id> следующей фазы]
```

## Outbound: auditor → founder (BLOCKED)

```
### HANDOFF auditor → founder · <phase> · <ISO-ts>
- task: post-audit BLOCKED
- did: аудит обнаружил неустранимый blocker
- artifacts: [_session-context/AUDIT-<date>-<phase>/AUDIT-REPORT.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: founder принимает решение (redesign / waive / cancel)
- escalate: <конкретный blocker + инвариант §6.N>
```

## Inbound: от verifier

```
### HANDOFF verifier → auditor · <phase> · <ISO-ts>
- task: verification PASS — запусти post-audit
- did: все AC проверены; tier фазы: <T>
- artifacts: [_session-context/VERIFY-<phase>-<ts>.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: auditor запускает <N>-линзовый аудит
- escalate: none
```
