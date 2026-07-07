---
gate: P6.5-production-deploy
status: pending
opened_at: "2026-07-07"
closed_at: null
founder_signature: null

hard_thresholds:
  iac_reproducible:
    target: "pass"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-1: terraform plan/validate/tflint 0 ошибок; ноль секретов в .tf/state (gitleaks/bandit на IaC)."
  residency_152fz:
    target: "pass"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-2: все ПД-ресурсы РФ-регион (ru-central1); compliance-чек-лист (compliance-152fz-specialist) пройден."
  secrets_lockbox:
    target: "pass"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-3: CD-манифест без секретов; всё через Lockbox; gitleaks/trivy зелёные."
  live_deploy_tls:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-4: terraform apply на реальном YC поднял стек; https://<domain>/health → 200 по TLS; managed-PG+pgvector доступен. BLOCKED до founder-ресурса (YC-аккаунт+домен)."
  cd_end_to_end:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-5: коммит в main → образ собран → задеплоен → health-check; откат проверен. BLOCKED до YC+CD."
  observability:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-6: ошибка backend в Sentry UI; событие в PostHog UI; метрики/логи собираются. BLOCKED до Sentry/PostHog."
  backup_restore:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    description: "AC-7: автоснапшот PG создан; восстановление в отдельный инстанс успешно (данные целы). BLOCKED до YC managed-PG."

deliverables:
  - id: D1
    name: "Terraform-модули (сеть, managed-PG+pgvector, Redis, compute, storage, registry)"
    status: pending
    owner: "devops-infra-specialist"
    notes: ""
  - id: D2
    name: "Домен + TLS + CD-pipeline (GH Actions → YCR → rolling deploy, Lockbox-секреты)"
    status: pending
    owner: "devops-infra-specialist"
    notes: ""
  - id: D3
    name: "Prod-observability (Sentry + PostHog + метрики/логи) + бэкапы PG + DR-проверка"
    status: pending
    owner: "devops-infra-specialist"
    notes: "PostHog снимает P1 DLG-1"
  - id: D4
    name: "152-ФЗ compliance-ревью резидентности + secrets-hygiene"
    status: pending
    owner: "compliance-152fz-specialist"
    notes: "NFR-1"

adr_delta:
  created: [ADR-0027]
  revised: []
  superseded: []

risks_delta:
  opened: []
  closed: []
  mitigated: []
  escalated: []
---

# Gate: P6.5 — Production deploy

## Rationale

Инфра-фаза (ADR-0027), поднимающая production на Yandex Cloud. P7 (публичный no-auth PLG) физически невозможен без прода — это первая монетизируемая точка и старт сбора кейсов (GTM §9.5). Закрывает NFR-1 (152-ФЗ резидентность на проде) и NFR-7 (PostHog). Исполняется параллельно с P6 (независимы, разные специалисты).

## Класс AC (ADR-0022)

- **mock-verifiable** (обязательны до PR, могут смёржиться раньше): iac_reproducible, residency_152fz, secrets_lockbox + tier-4 аудит IaC.
- **live-only** (blocked_pending_resource до founder-ресурса): live_deploy_tls, cd_end_to_end, observability, backup_restore. Требуют: YC-организация/folder, домен `BRAND_DOMAIN_RU`, токены YANDEX_CLOUD_*, DOCKER_REGISTRY_URL, POSTHOG_*, SENTRY_DSN (PLACEHOLDERS).

**Гейт не закрывается без live-only части.** Mock-verifiable подмножество (IaC + аудит) может быть смёржено, обеспечив готовность к деплою, но фаза считается завершённой только после живого деплоя.

## Checklist

- [ ] IaC воспроизводим (terraform plan/validate/tflint 0 ошибок, 0 секретов)
- [ ] 152-ФЗ резидентность (РФ-регион всех ПД-ресурсов) — compliance PASS
- [ ] Секреты из Lockbox (0 в пайплайне)
- [ ] Живой деплой + TLS (https health 200) — **live**
- [ ] CD end-to-end + откат — **live**
- [ ] Observability (Sentry + PostHog UI) — **live**
- [ ] Бэкап + восстановление проверены — **live**
- [ ] Аудит tier 4 PASS (5 линз)
- [ ] Founder закрыл gate (подпись)

## Sign-off

- **Статус:** pending
- **Подпись основателя:** _pending_
- **Дата:** _pending_
