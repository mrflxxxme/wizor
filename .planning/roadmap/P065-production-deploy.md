---
phase: P6.5
slug: production-deploy
title: "Production deploy — Yandex Cloud IaC + домен + TLS + CD + observability"
status: planned
tier: 4
track: infra
depends_on: [P1]
gated_by: []
contracts: []
specialists: [devops-infra-specialist, compliance-152fz-specialist]
prd_refs: [§9.3/NFR-1, §9.3/NFR-7, §12, §9.5]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): Инфра-фаза tier 4 (ADR-0027). Поднимает production на Yandex Cloud: Terraform IaC (managed PG+pgvector, Redis, compute, object storage), домен + TLS, CD-pipeline (GH Actions → YC Container Registry → rolling deploy, секреты из Lockbox), prod-observability (Sentry + PostHog self-host/cloud + мониторинг), бэкапы PG + DR, структурная 152-ФЗ-резидентность (ПД в РФ-регионе YC). Исполняется параллельно с P6; P7 зависит от неё. Живой деплой — live-only AC (ADR-0022). -->

## Goal

Поднять production-окружение WIZOR на Yandex Cloud, на которое встанет публичный Tier-0 (P7) и весь платный продукт (P9/P10). До этой фазы существует только dev-стек (`docker-compose.dev.yml`, P1) и CI — прода нет, все инфра-токены в PLACEHOLDERS = TODO. Фаза закрывает NFR-1 (152-ФЗ резидентность на проде) и NFR-7 (PostHog для North Star).

## In scope

- **Terraform IaC (Yandex Cloud):** VPC/подсети, managed Postgres 16 + pgvector, managed Redis, compute (VM или managed-k8s под нагрузку), object storage (бэкапы + evidence-скриншоты P8). Состояние Terraform — в YC object storage backend.
- **Домен + TLS:** регистрация/DNS `BRAND_DOMAIN_RU`, сертификаты (YC Certificate Manager / Let's Encrypt), автопродление.
- **CD-pipeline:** GitHub Actions → сборка Docker-образов → Yandex Container Registry → rolling-деплой; секреты **только** из Yandex Lockbox (не в CI-переменных, не в образах).
- **Prod-observability:** Sentry (backend+frontend error tracking), PostHog (self-host в YC или cloud — снимает P1 DLG-1), метрики (YC Monitoring / Prometheus+Grafana), structured JSON-логи с агрегацией.
- **Бэкапы + DR:** автоснапшоты managed-PG, retention-политика, **проверенное** восстановление (не только настроенное).
- **152-ФЗ структурно (NFR-1):** все хранилища ПД — в РФ-регионе YC; проверка, что зарубежная probe-egress-нода (Hetzner/Selectel) держит только stateless-прокси, без ПД. `compliance-152fz-specialist` подтверждает границу.
- **Secrets bootstrap:** Lockbox-хранилище, сервисный аккаунт CI/CD, ротация-политика.

## Out of scope

- Продуктовая функциональность (crawl/probe/score/recommendations) — это P2–P6, деплоятся этой инфрой, но не разрабатываются здесь.
- Auth/billing (P9), auto-fix (P10) — деплоятся позже по этому же CD.
- On-premise / Helm / multi-region (→ фаза C).
- Autoscaling/HA продвинутого уровня (стартовый прод — достаточная надёжность, не 99.9% SLA; SLA → фаза C).
- Зарубежная probe-инфра деталями (ноды есть с P5; здесь только подтверждение ПД-границы).

## Functional requirements

- **FR-P6.5-1 (NFR-1):** production ПД-хранилища (managed-PG, Redis, object storage) — в РФ-регионе Yandex Cloud; резидентность подтверждена структурно (Terraform-конфиг + compliance-ревью).
- **FR-P6.5-2 (§12):** воспроизводимая инфра — `terraform apply` из чистого состояния поднимает полный стек; ноль ручных кликов в консоли для core-ресурсов.
- **FR-P6.5-3 (CD):** мёрж в main → автоматический деплой образа в прод (rolling, с health-check gate); откат деплоя — одним действием.
- **FR-P6.5-4 (NFR-7):** PostHog в проде принимает события; Sentry ловит ошибки backend+frontend.
- **FR-P6.5-5 (DR):** бэкап PG создаётся автоматически; восстановление из бэкапа проверено (не только настроено).

## Acceptance criteria

- **AC-1 (IaC воспроизводим) [mock-verifiable]:** `terraform plan` из чистого состояния валиден (0 ошибок), `terraform validate` + `tflint` зелёные; ни один секрет не в `.tf`/state в открытом виде (bandit/gitleaks на IaC).
- **AC-2 (152-ФЗ резидентность) [mock-verifiable]:** тест конфигурации — все ПД-ресурсы имеют РФ-регион (`ru-central1`); compliance-чек-лист пройден (`compliance-152fz-specialist`).
- **AC-3 (secrets из Lockbox) [mock-verifiable]:** CD-манифест не содержит секретов; все чувствительные значения ссылаются на Lockbox; gitleaks/trivy на пайплайне зелёные.
- **AC-4 (живой деплой) [live-only]:** `terraform apply` на реальном YC-аккаунте поднял стек; `https://<BRAND_DOMAIN_RU>/health` → 200 по TLS; managed-PG с pgvector доступен приложению.
- **AC-5 (CD end-to-end) [live-only]:** тестовый коммит в main → образ собран → задеплоен → health-check прошёл; откат деплоя проверен.
- **AC-6 (observability) [live-only]:** реальная ошибка backend видна в Sentry UI; тестовое событие видно в PostHog UI; метрики/логи собираются.
- **AC-7 (бэкап+восстановление) [live-only]:** автоснапшот PG создан; восстановление из снапшота в отдельный инстанс успешно (данные целы).

## Contracts touched

- Контекстов домена не трогает — инфра под все контексты. Влияет на deploy-манифесты `iam`/`billing` и всех read-only контекстов (окружение исполнения).
- Раскрывает: production-окружение для P7 (публичный запуск), P9/P10 (платный/auto).

## Exit-gate

| Критерий | Порог | Класс |
|---|---|---|
| IaC воспроизводим | AC-1 (terraform plan/validate/tflint 0 ошибок) | mock-verifiable |
| 152-ФЗ резидентность | AC-2 (РФ-регион + compliance-чек) | mock-verifiable |
| Секреты из Lockbox | AC-3 (0 секретов в пайплайне) | mock-verifiable |
| Живой деплой + TLS | AC-4 | **live-only** (blocked_pending_resource: YC-аккаунт+домен) |
| CD end-to-end + откат | AC-5 | **live-only** |
| Observability | AC-6 (Sentry+PostHog UI) | **live-only** |
| Бэкап+восстановление | AC-7 | **live-only** |
| Аудит tier 4 | PASS (5 линз: correctness · security · compliance · tests · architecture) | — |

**Live-only AC блокированы до founder-ресурса** (ADR-0022): YC-организация/folder, домен, PLACEHOLDERS-токены (YANDEX_CLOUD_*, DOCKER_REGISTRY_URL, POSTHOG_*, SENTRY_DSN). Mock-verifiable подмножество (AC-1/2/3 + tier-4 аудит IaC) может быть смёржено раньше; гейт фазы не закрывается без live-only части.

## Decomposition hints for planner

1. `devops-infra-specialist` (Sonnet) пишет Terraform-модули (сеть, managed-PG+pgvector, Redis, compute, object storage, Container Registry).
2. `devops-infra-specialist` настраивает домен/DNS/TLS + CD-pipeline (GH Actions → YCR → rolling deploy, Lockbox-секреты).
3. `devops-infra-specialist` подключает Sentry + PostHog + мониторинг/логи; бэкап-политику PG + DR-проверку.
4. `compliance-152fz-specialist` (Opus) ревьюит резидентность (все ПД-ресурсы РФ-регион), stateless-границу зарубежной probe-ноды, secrets-hygiene.
5. `backend-implementer` адаптирует приложение под prod-конфиг (env из Lockbox, health/readiness-пробы, graceful shutdown).
6. Полный 5-линзовый аудит (tier 4) — фокус security (secrets, network) + compliance (152-ФЗ).
