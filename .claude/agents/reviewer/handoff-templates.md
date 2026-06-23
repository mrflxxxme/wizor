# reviewer — handoff templates

## Outbound: reviewer → verifier (approved)

```
### HANDOFF reviewer → verifier · <phase> · <ISO-ts>
- task: ревью завершено — approved
- did: запустил pr-review.md чек-лист, цикл <N>; 0 открытых findings
- artifacts: [revisions/<phase>-cycle<N>-reviewer.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: verifier запускает acceptance-тесты по AC из PLAN.md
- escalate: none
```

## Outbound: reviewer → implementer (revision)

```
### HANDOFF reviewer → <implementer> · <phase> · <ISO-ts>
- task: revision needed (цикл <N>)
- did: обнаружено <K> findings
- artifacts: [revisions/<phase>-cycle<N>-reviewer.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: implementer устраняет все findings, self-audit, коммит, хендофф назад
- escalate: none | security_flag: true — <краткое описание>
```

## Outbound: reviewer → architect (escalate после цикла 2)

```
### HANDOFF reviewer → architect · <phase> · <ISO-ts>
- task: эскалация — 2 цикла ревизии, findings не закрыты
- did: 2 цикла; незакрытые: <перечень issues>
- artifacts: [revisions/<phase>-cycle1-reviewer.md, revisions/<phase>-cycle2-reviewer.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: architect принимает решение / требует redesign
- escalate: <summary незакрытых issues>
```
