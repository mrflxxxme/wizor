---
id: ADR-0022
title: live-gold-resource-policy-and-ac-classification
status: accepted
date: 2026-07-07
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Каждый AC фазы классифицируется на mock-verifiable и live-only; live-only AC — явные gate-blocker'ы, не тихие deferred. Founder обязуется дать минимальный live-gold-набор (test-WP + funded LLM-ключи + зарубежная egress-нода) ДО старта P7 — иначе каскад deferred_live_gold растёт и подрывает доктрину evidence-gated. -->

## Context

Доктрина проекта — **evidence-gated scaling** (charter §1, PRD §3): автономность подтверждается результатами, а не зелёными моками. ADR-0018 ввёл live-gold перед PR, но допустил `deferred_live_gold` как клапан «где невозможно». К моменту P5 этот клапан использован уже трижды (P2 — test-WP; P4/P5 — funded LLM-ключи + зарубежная egress-нода), и впереди AC, которые моками непроходимы **в принципе**:

- **P7 AC-5** — реальные события в PostHog UI (`tier0_audit_started/completed`).
- **P9 AC-1** — e2e онбординг на тест-WP; **AC-3** — ЮKassa webhook (нужен sandbox).
- **P10 AC-1/AC-5** — JSON-LD появился/удалён в `<head>` реального WP-сайта (Playwright verify).

Без явной политики автономный цикл либо встаёт на verify, либо накапливает гору «зелёных» фаз, не проверенных вживую. И то и другое — провал: первое останавливает конвейер, второе создаёт иллюзию готовности. Усугубляет известный pitfall `test-masking` (MEMORY-INDEX: P4 AC-5, P5 brand_terms) — идеальный мок скрывает прод-баг.

## Decision

**Каждый AC фазы классифицируется на два класса, явно в phase-spec:**

1. **`mock-verifiable`** — проверяется детерминированным тестом/моком без внешних сервисов (unit+integration). Обязателен зелёный до PR (ADR-0018 без изменений).
2. **`live-only`** — проверяем только против реального внешнего сервиса (funded LLM, PostHog, ЮKassa sandbox, реальный WP, зарубежная egress-нода). Оформляется как **явный gate-blocker** в exit-gate фазы (строка со статусом `blocked_pending_resource`), НЕ как тихий `deferred_live_gold`.

**Ресурсная граница:** founder обязуется предоставить минимальный live-gold-набор **до старта P7** (первая монетизируемая точка): (а) founder-owned **test-WP URL**; (б) **funded LLM-ключи** (GigaChat/YandexGPT + OpenAI/Perplexity); (в) **зарубежная probe-egress-нода** + резидентный прокси; (г) PostHog-инстанс (self-host или cloud); (д) ЮKassa sandbox (для P9). Ориентир стоимости — 3–5 тыс ₽/мес (PLACEHOLDERS.md). До появления ресурса live-only AC явно `blocked`, фаза может быть смёржена по mock-verifiable подмножеству, но **exit-gate фазы не закрывается** без live-only части.

**Разметка ретроактивна:** phase-spec'и P6–P10 переписываются с колонкой класса на каждом AC (этот дроп).

## Consequences

- **Позитивно:** founder на гейте видит ровно, что проверено вживую, а что ждёт ресурса — ноль скрытого технического долга. Автономный цикл не встаёт (мёржит mock-verifiable часть), но и не врёт (live-only явно blocked).
- **Позитивно:** давление на своевременную поставку ресурсов — каскад deferred перестаёт расти молча, становится видимым списком в гейтах.
- **Компромисс:** фаза может быть «функционально готова, но не запущена» — состояние `merged, gate open on live-only`. Требует дисциплины в STATUS (rolling-трекер blocked-AC).
- **Риск:** если ресурсы не появятся к P7, конвейер логически доходит до P7 и там честно упирается — это by design (evidence-gated), не баг.
- **Открывает:** golden e2e-акцепт (ADR-0028) как финальную live-проверку связности — он по определению live-only.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Оставить как есть (`deferred_live_gold` ad-hoc) | Ноль работы | Каскад растёт молча; test-masking; иллюзия готовности | Подрывает evidence-gated доктрину |
| Стоп-режим: не начинать фазу с live-only AC без ресурса | Максимальная честность | Полная остановка конвейера при отсутствии ключей; frontend/backend-логика не пишется | Слишком жёстко: mock-verifiable часть можно и нужно строить заранее |
| Auto-fix только на mock, live отложить до Phase B | Быстрее MVP | P10 (moat) не доказан вживую → A→B gate H_autofix_reliability недостижим | Auto-fix — главный дифференциатор, его нельзя не проверить |

## Links

- Charter: `BUILD-CHARTER.md §12` (тестирование и live-gold)
- PRD: `PRD.md §3` (evidence-gated scaling), `§16` (открытые вопросы)
- Related ADRs: ADR-0018 (mandatory tests + live-gold — этот ADR ужесточает клапан deferred), ADR-0021 (evidence-протокол), ADR-0028 (golden e2e)
