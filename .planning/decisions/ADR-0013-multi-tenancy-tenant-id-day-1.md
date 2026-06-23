---
id: ADR-0013
title: multi-tenancy-tenant-id-day-1
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): tenant_id вводится с первого дня во всех таблицах данных; изоляция тенантов = стоячий инвариант; переход в agency-режим (фаза B) без миграции архитектуры. -->

## Context

MVP целится в SMB self-serve (сценарий A), но phase B — agency white-label (один аккаунт агентства → N клиентских сайтов). Ретрофит multi-tenancy после запуска = миграция всей БД и риск data-leak. Фаза B начинается уже на мес. 6–9 фазы A. Нужно заложить изоляцию с дня 1, не усложняя MVP-UX для single-tenant клиентов.

## Decision

Все таблицы данных содержат **`tenant_id UUID NOT NULL`** с дня 1. Keycloak realm = organizational unit; при SMB single-tenant `tenant_id` = user's own org. В MVP agency-UX и billing не строятся, но **схема данных изолирует тенантов**: нет cross-tenant запросов без явного `WHERE tenant_id = ?`; RLS (Row Level Security) в Postgres активируется при переходе в agency (фаза B).

Нарушение изоляции тенантов = стоячий инвариант №8 в Charter §6; проверяется каждым аудитом.

## Consequences

- Переход в agency-режим (фаза B) не требует миграции схемы; только добавление agency-UX и billing-слоя.
- Row Level Security включается в фазе B без изменения application-кода запросов.
- Нет риска cross-tenant data leak с дня 1.
- Компромисс: небольшой overhead в каждом запросе на tenant_id-фильтрацию; несущественен при MVP-нагрузках.
- Все boundedcontext-контракты в `.planning/contracts/` должны включать `tenant_id` в поля схемы.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| tenant_id вводить в фазе B | MVP проще | Миграция всей БД = высокий риск; data leak в переходный период | Цена ретрофита > overhead MVP |
| Отдельная БД/schema на тенанта | Максимальная изоляция | Operational nightmare при 100+ тенантах | Qdrant/pgvector-поддержка сложнее; оверинжиниринг |
| Нет multi-tenancy вообще | Простота | Фаза B невозможна без переписывания | Закрывает agency-сценарий |

## Links

- Charter: `BUILD-CHARTER.md §6 (инвариант 8), §7 (ctx: iam)`
- PRD: `PRD.md §9.2 (FR-6.2), §10`
- Related ADRs: ADR-0011 (stack), ADR-0015 (trust ladder)
