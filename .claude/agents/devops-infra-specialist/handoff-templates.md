# devops-infra-specialist — handoff templates (charter §8.6)

## Outbound → backend-implementer (env + конфиги P1)

```
### HANDOFF devops-infra-specialist → backend-implementer · P1 · <ISO-ts>
- task: env-переменные и конфиги для backend
- did: Yandex Cloud поднят; Lockbox настроен; CI зелёный; git grep secrets = 0
- artifacts: [infra/docker-compose.yml, .env.example, ci/.gitlab-ci.yml]
- contracts_touched: [iam]
- self_audit: pass  (нет `latest` тегов в prod; secrets = 0 в коде)
- next: backend-implementer использует env-шаблон
- escalate: none
```

## Outbound → crawler-probe-specialist (зарубежные ноды P5)

```
### HANDOFF devops-infra-specialist → crawler-probe-specialist · P5 · <ISO-ts>
- task: зарубежные probe-ноды готовы
- did: Hetzner/Selectel VPS; сетевая изоляция; IP = non-RF подтверждено
- artifacts: [infra/probe-nodes-topology.md]
- contracts_touched: [probe]
- self_audit: pass
- next: crawler-probe-specialist подключает probe к зарубежным нодам
- escalate: none | nodes_unavailable — ноды не отвечают
```
