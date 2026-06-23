---
id: ADR-0014
title: dual-geo-probe-no-ru-ip
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Probe-инфра разнесена гео: RU-ноды для RU-моделей (Алиса/GigaChat), зарубежные ноды + резидентные прокси для ChatGPT/Perplexity; ни один probe к ChatGPT/Perplexity — с РФ-IP. -->

## Context

WIZOR мониторит 4 LLM-провайдера: Алиса/Нейро + GigaChat (RU API, Yandex Cloud Foundation Models / GigaChat API) и ChatGPT/Perplexity (глобальные сервисы). Проблема: ChatGPT/Perplexity из РФ-IP либо недоступны, либо дают локализованные (RU-filtered) ответы, непригодные для объективного мониторинга. NFR-2 требует dual-geo с дня 1.

## Decision

Probe-инфра разнесена:
- **RU-ноды** (Yandex Cloud, РФ): Алиса/Нейро через Yandex Cloud Foundation Models API; GigaChat через GigaChat API. ПД клиентов не покидают РФ.
- **Зарубежные ноды** (Hetzner/Selectel): ChatGPT (OpenAI API) и Perplexity (Perplexity API) + web-scraping fallback. Резидентные прокси (Smartproxy/Bright Data) для ротации.

**Абсолютное правило (стоячий инвариант №4 Charter §6):** ни один probe-запрос к ChatGPT/Perplexity не выполняется с РФ-IP — ни напрямую, ни через RU-прокси. Нарушение = BLOCKED в аудите.

httpx + tenacity: retry/ротация прокси; сбои изолированы (не роняют весь батч).

## Consequences

- Объективные ответы ChatGPT/Perplexity из «мирового» контекста; нет РФ-фильтрации.
- ПД клиентов (контент сайта, токены) обрабатываются только на RU-нодах для RU-моделей — 152-ФЗ compliant.
- Операционный overhead: поддержка двух инфра-кластеров с дня 1; оправдано требованием мониторинга всех 4 провайдеров.
- Компромисс: Hetzner/Selectel ноды — дополнительные расходы (~$50–100/мес на старте).
- crawler-probe-specialist и devops-infra-specialist совместно владеют этим решением.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Только RU-ноды для всех провайдеров | Дешевле, проще | ChatGPT/Perplexity недоступны / дают неточные ответы | Нарушает NFR-2; делает мониторинг бесполезным |
| VPN с РФ-IP → зарубежные сервисы | Дёшево | Ненадёжно; блокируется; технически РФ-IP | Нарушает инвариант №4 |
| Только ChatGPT + Perplexity (без RU-моделей) | Просто | Потеря главного RU-дифференциатора | Алиса/GigaChat — moat против глобальных конкурентов |

## Links

- Charter: `BUILD-CHARTER.md §6 (инвариант 4)`
- PRD: `PRD.md §9.3 (NFR-2), §9.2 (FR-2.2), §12 (Crawler/probe, Инфра)`
- Related ADRs: ADR-0011 (stack), ADR-0013 (multi-tenancy)
