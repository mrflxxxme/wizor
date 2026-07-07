---
id: ADR-0027
title: production-deploy-phase
status: accepted
date: 2026-07-07
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Вводится отдельная инфра-фаза P6.5 «Production deploy» (tier 4, devops-infra-specialist): Terraform на Yandex Cloud + домен + TLS + CD-pipeline + бэкапы PG + prod-мониторинг (Sentry/PostHog). P7 (публичный no-auth PLG) физически невозможен без прода, но развёртывание не было ничьим scope — P1 дал только repo/CI/docker-compose. P6.5 исполняется параллельно с P6; вклад founder — YC-аккаунт/домен/токены из PLACEHOLDERS. -->

## Context

P7 — публичный no-auth PLG-вход (лендинг, реальные пользователи, PostHog-воронка) — первая монетизируемая точка. Но развёртывание на production (Yandex Cloud: VM/managed-k8s, домен, TLS, Terraform/IaC, prod-мониторинг, бэкапы Postgres, секреты в Lockbox) не было ничьим scope. P1 дал только repo/CI/`docker-compose.dev.yml` (dev-стек); все инфра-токены в PLACEHOLDERS — TODO. Это самый недооценённый блокер «рабочего продукта»: без прода P7 невозможен, а он — точка старта монетизации и сбора кейсов (GTM §9.5). NFR-1 (152-ФЗ: ПД в РФ, Yandex Cloud) — обязателен именно на проде, не в dev.

## Decision

**Отдельная инфра-фаза `P6.5 — Production deploy`** (tier 4, track `infra`, specialist `devops-infra-specialist` + `compliance-152fz-specialist` для NFR-1):

- **IaC:** Terraform на Yandex Cloud — сети, managed Postgres (pgvector), managed Redis, compute (VM или managed-k8s), object storage (бэкапы/evidence-скриншоты).
- **Домен + TLS:** регистрация/DNS `BRAND_DOMAIN_RU`, сертификаты (Let's Encrypt / YC Certificate Manager).
- **CD-pipeline:** GitHub Actions → сборка образов → Yandex Container Registry → деплой (rolling); secrets из Yandex Lockbox (не в CI-переменных).
- **Prod-observability:** Sentry (backend+frontend error tracking), PostHog (self-host или cloud — снимает P1 DLG-1), Prometheus/Grafana или YC Monitoring, structured logs.
- **Бэкапы + DR:** автоматические снапшоты managed-PG, retention-политика, проверка восстановления.
- **152-ФЗ на проде:** резидентность РФ подтверждена структурно (все ПД-хранилища в YC РФ-регионе); зарубежная probe-egress-нода (Hetzner/Selectel) — только stateless-прокси, без ПД.

- **Зависимости:** `depends_on: [P1]`; исполняется **параллельно** с P6 (независимы). `gated_by: []`.
- **P7 получает `depends_on: [..., P6.5]`** — публичный запуск требует прода.
- **Вклад founder (блокер live-части):** YC-организация/folder, домен, критичные PLACEHOLDERS-токены (YANDEX_CLOUD_*, DOCKER_REGISTRY_URL, POSTHOG_*, SENTRY_DSN). Живой деплой — live-only AC (ADR-0022).

## Consequences

- **Позитивно:** «рабочий продукт» получает точку запуска; P7 PLG-воронка и сбор кейсов (GTM) разблокированы; 152-ФЗ-резидентность реализована там, где она реально применяется (прод).
- **Позитивно:** инфра-фаза изолирована — свой tier-4 аудит (security+compliance фокус), не смешана с продуктовым PLG-кодом P7.
- **Позитивно:** параллельность с P6 не удлиняет критический путь (P6 — продуктовый, P6.5 — инфра, разные специалисты).
- **Компромисс:** требует реальных YC-аккаунтов и трат до P7 — но это неизбежно для запуска и уже в PLACEHOLDERS как предусловие прода.
- **Компромисс:** нумерация «P6.5» вне целочисленного ряда — но точнее отражает «между P6 и P7, параллельно P6», чем вставка P7→P8 сдвигом всех номеров.
- **Открывает:** managed-инфра переиспользуется всеми последующими фазами; CD-pipeline — для непрерывного деплоя P7–P10.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Включить prod-deploy в scope P7 | Без новой фазы | P7 разбухает (PLG-продукт + вся инфра в одном цикле); смешанный аудит; критический путь удлиняется | Инфра и продукт — разные tier/специалисты/линзы |
| Деплой после P9 (один раз перед запуском) | Всё оттестировано локально/CI | PLG-воронка P7 и сбор кейсов откладываются на месяцы; поздняя интеграция с реальной инфрой | GTM требует Tier-0 в проде рано |
| Сдвинуть номера (P7→P8…) вставив целую фазу | Целочисленный ряд | Ломает все depends_on/ссылки в 10 спеках + памяти | P6.5 дешевле и точнее по смыслу (параллельно P6) |

## Links

- Charter: `BUILD-CHARTER.md §5` (роадмап), §6 (инвариант §6.6 ПДн-резидентность)
- PRD: `PRD.md §9.3` (NFR-1 152-ФЗ, NFR-7 PostHog), §12 (стек: Yandex Cloud), §9.5 (GTM)
- Related ADRs: ADR-0011 (стек-lock), ADR-0022 (live-only deploy AC), ADR-0013 (multi-tenancy)
- Phase-spec: `roadmap/P065-production-deploy.md`; gate `gates/P065-production-deploy.md`
- PLACEHOLDERS: YANDEX_CLOUD_*, DOCKER_REGISTRY_URL, BRAND_DOMAIN_RU, POSTHOG_*, SENTRY_DSN
