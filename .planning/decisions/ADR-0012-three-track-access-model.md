---
id: ADR-0012
title: three-track-access-model
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Три дорожки доступа: Tier 0 (no-auth PLG), Manual (без API, read-only), Auto (API+DPA); DPA/API — gate только Auto, не входа в продукт. -->

## Context

Главный риск-гипотеза H1: клиенты не готовы давать write-API-доступ к production-сайту. Если auto-fix — условие входа в продукт, продукт не монетизируется до подтверждения H1. Нужна модель, при которой продукт имеет реальную ценность без write-доступа, а auto-fix становится upgrade-путём, а не порогом.

## Decision

**Три дорожки доступа** (PRD §4.1):

| Дорожка | Доступ | Что входит |
|---|---|---|
| **Tier 0 — Instant Audit** | URL, no-auth | AI-Readiness Score + competitive gap + copy-paste патчи + базовая Visibility |
| **Manual track** | без API (read-only) | + регулярный мониторинг, прио-рекомендации, патчи копипастом, re-crawl верификация |
| **Auto track** | API + DPA | + авто-применение машиночитаемого слоя, FAQ через review, rollback, closed-loop attribution |

**DPA/API — gate только Auto track**, не входа в продукт. Аудит, патчи, probe, re-crawl-верификация работают полностью read-only. Видимый контент (FAQ) не авто-применяется ни в каком track'е без review.

Дорожки соответствуют инварианту 1 из Charter §6 (read-only-граница) и проверяются auditor'ом при каждом аудите.

## Consequences

- Tier 0 = PLG-лид-магнит без регистрации; снижает CAC.
- Manual track монетизируется независимо от H1; де-рискует P&L.
- Auto track = premium upgrade с data-flywheel (closed-loop attribution → обучение предиктивной модели).
- Компромисс: тройная дорожка усложняет UX-онбординг; нужно чёткое позиционирование в UI.
- Инвариант «ноль write в Tier 0/Manual» проверяется как стоячий инвариант №1 в каждом аудите.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Только Auto track | Максимальный moat | Нет ценности без H1; риск нулевой монетизации | Противоречит evidence-gated doctrine |
| Freemium без Tier 0 | Меньше нагрузки | Нет PLG-воронки; выше CAC | Tier 0 = лид-магнит без стоимости привлечения |
| Manual = бесплатный, Auto = платный | Простота tier'инга | Manual имеет ценность (мониторинг); должен монетизироваться | Два платных track'а, оба обоснованы |

## Links

- Charter: `BUILD-CHARTER.md §2 (#16), §6 (инвариант 1)`
- PRD: `PRD.md §4.1, §9.1, §9.4, §3 (p.8)`
- Related ADRs: ADR-0007 (roadmap), ADR-0015 (trust ladder)
