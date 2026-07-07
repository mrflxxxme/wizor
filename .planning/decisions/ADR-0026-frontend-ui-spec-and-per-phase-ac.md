---
id: ADR-0026
title: frontend-ui-spec-and-per-phase-ac
status: accepted
date: 2026-07-07
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): Frontend был крупнейшей дырой спеки: P6/P8 без frontend-scope, авторизованный кабинет не специфицирован нигде, во фронте только скелет P1. Решение: единый инвентарь экранов `.planning/UI-SPEC.md` (экраны/состав/навигация/компонентная база словами, без пиксельных макетов) + frontend-scope и frontend-AC вшиты в каждую фазу P6–P10 — каждая фаза отгружает свой UI-инкремент вместе с API. -->

## Context

Аудит документации выявил, что frontend — крупнейший пробел «рабочего продукта». Факты: P6 (рекомендации) и P8 (верификация/тренды/алерты) не имели frontend-scope вообще; авторизованный кабинет (Score-дашборд, список рекомендаций с copy-paste патчами, тренд-график с полосой шума, настройки алертов, approve-очередь auto-fix, FAQ-review экран, audit log/rollback, DPA-флоу) не специфицирован нигде; во frontend-коде — только скелет P1 (Next.js app-router + PostHog no-op + North Star константы). Без этого backend будет готов, а пользоваться нечем — MVP не «рабочий продукт». Ранее frontend упоминался лишь фрагментарно в P7 (landing+result) и P9 (онбординг/биллинг).

## Decision

**Два взаимодополняющих артефакта:**

1. **`.planning/UI-SPEC.md`** — компактный инвентарь всех экранов MVP: карта экранов (роут/auth/фаза/назначение), состав каждого экрана словами (блоки/поля/состояния/PostHog-события/enforced-инварианты), навигация, переиспользуемая компонентная база (ScoreGauge, PatchCard, TrendChart с CI-band, ForecastBadge, ApproveQueueItem, DpaGate…), таблица соответствия экранов фазам. Без пиксельных макетов и CSS — детали компонентов JIT при планировании фазы. База — shadcn/ui.

2. **Frontend-scope + frontend-AC в каждой фазе P6–P10.** Каждая фаза отгружает свой UI-инкремент **вместе** с API, не откладывая на «UI-фазу в конце». Раскладка:
   - **P6** — первый авторизованный кабинет: dashboard (Score+компоненты), recommendations (прио-список+copy-paste патчи), competitive gap.
   - **P7** — публичные: landing (URL-инпут), Tier-0 result (async прогресс-страница, ADR-0025).
   - **P8** — visibility trends (тренд-график с полосой шума, «нет ложных побед»), alert settings.
   - **P9** — login/register (Keycloak OIDC), onboarding wizard (+ prompt-set редактор, ADR-0024), billing (3 тарифа × Manual/Auto).
   - **P10** — auto-fix approve queue (trust-ladder), FAQ review screen (staging→подтверждение, авто-публикация заблокирована), audit log + 1-click rollback, DPA acceptance flow.

**UI-инвариант (enforced в каждом frontend-ревью):** нигде не показывается гарантированный Visibility-% — всегда диапазон + confidence + disclaimer (инвариант §6.2 charter). `geo-domain-expert` ревьюит понятность Score/forecast/CTA.

## Consequences

- **Позитивно:** «рабочий продукт» становится достижимым — к концу каждой фазы есть кликабельный инкремент, а не только API. Интеграция UI↔API идёт непрерывно, без большого водопадного куска в конце.
- **Позитивно:** honest-forecast инвариант получает исполняемую точку контроля в UI (ForecastBadge), не только в backend-схеме.
- **Компромисс:** каждая фаза P6–P10 тяжелеет на frontend-задачи → `frontend-implementer` вовлечён почти в каждую фазу (раньше — только P7/P9). Оправдано: инкрементальный UI дешевле большого позднего.
- **Компромисс:** UI-SPEC — ещё один документ для поддержки. Митигируется тем, что он инвентарь (стабилен), детали — JIT.
- **Открывает:** консистентный дизайн-язык через компонентную базу; переиспользование компонентов между фазами.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Отдельная UI-фаза «P8.5 Dashboard» со всем кабинетом сразу | Фокус, один аудит UI | Поздняя интеграция UI↔API (большой водопад); backend-фазы «слепые» до неё | Риск рассинхрона; инкремент лучше |
| Минимальный UI только в P7/P9 | Быстрее MVP | Тренды/алерты/approve-очередь без UI до фазы B → продукт сырой для платящих | «Рабочий продукт» не собирается |
| Пиксельные макеты (Figma) в спеке | Точность дизайна | Дорого, преждевременно для соло-фаундера; устаревают | Инвентарь словами достаточен для frontend-implementer |

## Links

- Charter: `BUILD-CHARTER.md §6` (инвариант §6.2 honest-forecast), §8 (форматы)
- PRD: `PRD.md §4.1, §5` (North Star/PostHog), §9.1 (scope MVP)
- Related ADRs: ADR-0025 (async Tier-0 result), ADR-0024 (prompt editor), ADR-0011 (стек: Next.js/shadcn)
- Артефакт: `.planning/UI-SPEC.md`
