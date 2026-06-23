# compliance-152fz-specialist — handoff templates (charter §8.6)

## Outbound → агент (вердикт)

```
### HANDOFF compliance-152fz-specialist → <agent> · <phase> · <ISO-ts>
- task: compliance-вердикт по [провайдер/архитектура/DPA/audit log]
- did: проверка 152-ФЗ + dpa-and-residency.md
- artifacts: [memory/compliance-verd-{date}.md]
- contracts_touched: [<контекст>]
- self_audit: pass
- next: <agent> продолжает / блокируется
- escalate: none | founder_required
```

## Outbound → cms-connector-specialist (DPA)

```
### HANDOFF compliance-152fz-specialist → cms-connector-specialist · P10 · <ISO-ts>
- task: DPA-подтверждение для auto-fix
- did: акцепт зафиксирован; версия DPA = X
- artifacts: [dpa_record: {tenant_id, version, accepted_at}]
- contracts_touched: [autofix]
- self_audit: pass
- next: cms-connector активирует auto-fix
- escalate: none
```

## Outbound → founder (эскалация)

```
### HANDOFF compliance-152fz-specialist → founder · <phase> · <ISO-ts>
- task: юридическое решение
- did: противоречие вне технических требований
- artifacts: [reports/compliance-issue-{date}.md]
- contracts_touched: [<контекст>]
- self_audit: fail
- next: founder решает
- escalate: legal_judgment_required — <описание>
```
