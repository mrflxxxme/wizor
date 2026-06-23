# cms-connector-specialist — handoff templates (charter §8.6)

## Outbound → backend-implementer (после P10 plugin)

```
### HANDOFF cms-connector-specialist → backend-implementer · P10 · <ISO-ts>
- task: интеграция WIZOR backend ↔ WP plugin REST API
- did: WP plugin: apply-patch/rollback endpoints; audit log append-only; idempotency via hash
- artifacts: [connectors/wordpress/wizor-plugin/, api/wp-connector.yaml]
- contracts_touched: [connectors, autofix]
- self_audit: pass  (FAQ auto-apply заблокирован; DPA-чек на каждый вызов; нет credentials в коде)
- next: backend-implementer создаёт client к WP plugin API
- escalate: none
```

## Outbound → compliance-152fz-specialist (ревью audit log)

```
### HANDOFF cms-connector-specialist → compliance-152fz-specialist · P10 · <ISO-ts>
- task: ревью схемы audit log на 152-ФЗ
- did: схема wizor_audit_log определена; INSERT-only constraint
- artifacts: [db/migrations/audit_log.sql]
- contracts_touched: [autofix]
- self_audit: pass
- next: compliance-152fz-specialist проверяет retention, immutability
- escalate: none
```
