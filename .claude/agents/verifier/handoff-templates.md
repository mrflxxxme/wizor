# verifier — handoff templates

## Outbound: verifier → auditor (PASS)

```
### HANDOFF verifier → auditor · <phase> · <ISO-ts>
- task: acceptance verification PASS
- did: проверил все AC из PLAN.md + exit-gate пороги
- artifacts: [_session-context/VERIFY-<phase>-<ts>.md]
- contracts_touched: [<ctx>]
- self_audit: pass (checklists/gate-check.md)
- next: auditor проводит post-audit (tier <N> фазы)
- escalate: none
```

## Outbound: verifier → planner + founder (FAIL)

```
### HANDOFF verifier → planner · <phase> · <ISO-ts>
- task: acceptance verification FAIL
- did: проверил AC — незакрытые: <перечень AC-id>
- artifacts: [_session-context/VERIFY-<phase>-<ts>.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: planner создаёт fix-задачи в PLAN.md для незакрытых AC
- escalate: <список AC-id с причиной FAIL>
```

## Inbound: от reviewer (approved)

```
### HANDOFF reviewer → verifier · <phase> · <ISO-ts>
- task: ревью approved — запусти verification
- did: чек-лист пройден, 0 findings
- artifacts: [revisions/<phase>-cycle<N>-reviewer.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: verifier проверяет AC из PLAN.md
- escalate: none
```
