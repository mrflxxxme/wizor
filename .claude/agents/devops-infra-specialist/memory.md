# devops-infra-specialist — memory

## Namespace

`memory/devops-infra-specialist.md`

## MUST-persist

- **Инфра-топология**: текущая схема Yandex Cloud + зарубежные ноды (без credentials)
- **Docker image registry**: актуальные теги prod/staging
- **CI-пайплайн версии**: текущие конфиги GitLab CI / GitHub Actions
- **Runbook**: процедуры при инцидентах (YC недоступен, ноды отвалились)
- **Rate-limit конфиги**: текущие лимиты Tier-0 + история изменений
- **Известные инфра-проблемы**: паттерны отказов, митигации

## MUST-NOT persist

- Secrets/credentials (только Vault/Lockbox)
- IP-адреса прокси (только в Vault)

## Retrieval queries

- «Текущая инфра-топология»
- «Runbook для [тип инцидента]»
- «Rate-limit конфиг Tier-0»

## Write triggers

- После каждого инфра-изменения: обновить топологию.
- После инцидента: добавить в runbook.
- `memory-curator` пишет после шага 8.

## Pruning

- Устаревшие Docker-теги (>3 версии назад) → архивировать.
- Runbook записи старше 12 месяцев → review и обновить.
