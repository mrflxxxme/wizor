# memory-curator — handoff templates

## Outbound: memory-curator → founder (готово к PR)

```
### HANDOFF memory-curator → founder · <phase> · <ISO-ts>
- task: шаг 8 цикла завершён — фаза готова к PR
- did: обновил STATUS/HANDOFF/JOURNAL/MEMORY-INDEX/memory/gate/README; архив аудита
- artifacts: [.planning/STATUS.md, .planning/HANDOFF.md, .planning/MEMORY-INDEX.md, README.md]
- contracts_touched: []
- self_audit: pass (checklists/memory-update.md)
- next: founder создаёт PR; tier-based merge
- escalate: none | gate_pending: [<поля не заполнены>]
```

## Outbound: memory-curator → founder (конфликт данных)

```
### HANDOFF memory-curator → founder · <phase> · <ISO-ts>
- task: конфликт данных при записи состояния
- did: обнаружил несоответствие между аудит-отчётом и текущим STATUS
- artifacts: [.planning/STATUS.md, _session-context/AUDIT-<date>-<phase>/AUDIT-REPORT.md]
- contracts_touched: []
- self_audit: n/a (blocked)
- next: founder разрешает конфликт вручную
- escalate: <конкретное несоответствие>
```

## Inbound: от auditor

```
### HANDOFF auditor → memory-curator · <phase> · <ISO-ts>
- task: post-audit завершён — выполни шаг 8
- did: аудит PASS/PASS-WITH-FIXES
- artifacts: [_session-context/AUDIT-<date>-<phase>/AUDIT-REPORT.md]
- contracts_touched: [<ctx>]
- self_audit: pass
- next: memory-curator обновляет все 8 файлов состояния
- escalate: none
```
