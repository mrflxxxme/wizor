<!-- HEAD-SUMMARY (≤500т): Обзор роадмапа WIZOR P0–P10. Таблица зависимостей фаз (из charter §5). Обоснование read-only-first архитектуры. Рамочное описание Phase B (Agency white-label) и Phase C (Enterprise + Integration layer) с exit-gates из PRD §10–11 и §8. Критерии A→B gate. -->

# WIZOR — Roadmap (фазы A, B, C)

> Документ-обзор. Полные спецификации — в `.planning/roadmap/PNN-*.md`. История выполнения — в `.planning/PHASE-HISTORY.md`.

---

## P0–P10: таблица зависимостей (Phase A — MVP)

| Фаза | Название | Track | Tier | depends_on | gated_by | Ключевые FR/контракты |
|---|---|---|---|---|---|---|
| **P0** | Discovery & De-risking (H1–H5) | research | — | — (параллельно P1–P5) | — | §9.0: 30 интервью + 4 спайка |
| **P1** | Foundation | infra | 4 | — | — | NFR-1,7; FR-6.2 → `iam` |
| **P2** | Crawler / Аудит | read-only | 3 | P1 | — | FR-1.1, FR-1.2 → `crawler`, `scoring` |
| **P3** | AI-Readiness Score | read-only | 3 | P2 | — | FR-1.3 → `scoring` |
| **P4** | LLM-router | infra | 4 | P1 | — | NFR-3 → `llm-router` |
| **P5** | Probe-мониторинг | read-only | 3 | P4 | — | FR-2.1–2.4 → `probe`, `metrics` |
| **P6** | Рекомендации | read-only | 3 | P3, P5 | — | FR-3.1–3.5 → `recommendations`, `patches` |
| **P7** | ⭐ Tier 0 Instant Audit | read-only | 3 | P2,P3,P4,P5,P6 | — | §4.1, §9.1 → публичный PLG |
| **P8** | Верификация | read-only | 3 | P6 | — | FR-5.1–5.5 → `verification`, `notifications` |
| **P9** | Auth + биллинг + дорожки | infra | 4 | P7, P8 | — | FR-6.1–6.3, §9.4 → `iam`, `billing` |
| **P10** | ⭐ Auto track | auto | 4 | P9 | **P0** | FR-4.1–4.7 → `autofix`, `connectors` |

**Параллельность:** P0 идёт одновременно с P1–P5. P2 и P4 независимы — могут идти параллельно после P1.

---

## Read-only-first: обоснование архитектурного принципа

**Ключевая идея (PRD §4.1, доктрина §3, п. 8):** аудит, готовые патчи, базовая Visibility и даже верификация применённого через re-crawl работают **по одной ссылке без доступа к сайту**. Доступ на запись нужен ровно для одного: автоматически внести правку.

Это даёт три стратегических эффекта:

1. **Снятие барьера входа.** Пользователь получает ценность сразу (Tier 0 no-auth, Manual track), без необходимости давать API-доступ к production-сайту.
2. **Де-риск гипотезы H1** (риск №1 тезиса: «клиенты не дадут API»). Даже если H1 = no-go, продукт монетизируется через Manual track. Auto track — апгрейд, а не порог входа.
3. **Compliance by design.** Читать чужой сайт (публичные данные) — не обработка ПД. Записывать на сайт — совсем другой режим (DPA gate, FR-4.6).

**Следствие для порядка фаз:** P2–P8 полностью read-only → реализуются до P10 (Auto track). P10 gated_by P0 (гипотезы H1+H5 подтверждены). Монетизация стартует на P7 (Tier 0 бесплатный) и P9 (Manual/Auto платный).

---

## Phase B — Agency white-label (рамочно, §10 PRD)

### Цель
Платформа для SEO/SERM-агентств (≈500 в РФ), продающих GEO под своим брендом. Дифференциация от Шпиониро — auto-fix + качество CMS-интеграций.

### Ключевой scope (уточняется на A→B gate)
- Multi-tenant: аккаунт агентства → N клиентских сайтов; роли `agency_admin` / `agency_seo` / `client_viewer`.
- White-label кабинет (домен, логотип, цвета, footer).
- Agency-billing: счета на агентство, договоры с НДС, РФ-юрлицо; Stripe для экспортных.
- Bulk-операции: аудит/генерация по 50 сайтам; API для агентских интеграций.
- Отчётность: PDF/PPTX с шильдиком, competitive benchmarking, sentiment-трекинг.
- CMS: WordPress, Tilda, Bitrix, 1C-Битрикс, Modx, OpenCart (+ Shopify для экспортных).
- Партнёрская программа, образовательный контент (certified GEO-specialist).

### Exit-gate B→C (все условия, PRD §8)
1. Adoption агентств доказан (N агентств, NRR > целевого порога).
2. Enterprise-pull: подписанные LOI/пилоты.
3. Спрос на Integration layer (MCP/embeddings) валидирован на конкретных клиентах.
- **Pivot-дедлайн:** явное решение go/pivot/stop при не достижении.

**Метрика-ориентир:** MRR 8–12M ₽ к ~мес. 9 Phase B.

---

## Phase C — Enterprise + Integration layer (рамочно, §11 PRD)

### Цель
Полноценная «AI Readiness Platform», единственная в РФ, закрывающая все 3 уровня доступности (Discovery + Comprehension + Integration).

### Ключевой scope (уточняется на B→C gate, требует доп. дискавери)
- Production-ready коннекторы: Bitrix24, 1C-Битрикс, Magento (Adobe Commerce), InSales, Shopify Plus, headless (Strapi/Contentful/Sanity).
- **MCP-сервер на сайт** (`@modelcontextprotocol/sdk`): эндпоинты `product_search` / `content_query` / `knowledge_base`. *(Спрос подтверждён глобально; «MCP на маркетинг-сайт» — гипотеза, отдельный дискавери.)*
- Public content API (REST + GraphQL), LLM-export endpoints (`/llm-context.md`), webhook content sync.
- **llms.txt / llms-full.txt** в полном масштабе (настоящий дом — Integration layer, не citation-фактор).
- Embeddings as a service (multilingual-e5-large, BGE-M3, Yandex/GigaChat Embeddings); Vector DB (Qdrant self-host).
- Agent-friendly forms (ARIA), product feeds (Я.Маркет, Wildberries, Ozon Seller API, Google Shopping).
- **A/B-тестирование AI-видимости** (статистический модуль).
- On-premise (Helm/K8s) для банков/госзаказа; SLA 99,9%; dedicated CSM.

**Метрика-ориентир:** ARR 60–120M ₽ через 24 мес (10–20 enterprise-клиентов).

---

## A→B gate — критерии перехода (PRD §8)

Все 5 условий должны быть выполнены:

| # | Критерий | Тип | Источник данных |
|---|---|---|---|
| 1 | ≥ N сайтов с **verified Readiness-uplift** и наблюдаемым Visibility-сдвигом на ≥1 retrieval-поверхности | Evidence | P8 verification data |
| 2 | **Готовность давать API-доступ / подписывать DPA** доказана на реальной выборке | Evidence | P10 DPA-records, P0/H1+H5 |
| 3 | Надёжность auto-fix: rollback-rate ниже порога; **0 инцидентов порчи production** | Guardrail | P10 audit-log |
| 4 | **Пол MRR + сигнал retention** (M3-retention ≥ целевого) | Business | P9 billing data |
| 5 | **Входящий интерес ≥ 3–5 агентств** | GTM | CRM, inbound leads |

**Pivot-дедлайн (мес. 9 Phase A):** если gate не достигнут → явное решение: pivot в чистый agency-tool / сужение ICP / stop.

---

*ROADMAP.md v1.0 · 2026-06-23 · читается build-агентами для контекста фаз. Детали каждой фазы — в `.planning/roadmap/PNN-*.md`.*
