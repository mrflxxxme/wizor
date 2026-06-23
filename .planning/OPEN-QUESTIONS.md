<!-- HEAD-SUMMARY (≤500т): Реестр 9 открытых вопросов и гипотез WIZOR из PRD §16. Вопросы по: custdev P0 (H1–H5), достоверности входных метрик, составу весов AI-Readiness Score, retrieval-механике Яндекс Нейро/Алисы, MCP-на-маркетинг-сайт (фаза C), длительности trial, порогу trust-ladder auto-apply, конверсии воронки Tier 0→Manual→Auto, предиктивной Visibility-модели. -->

# OPEN-QUESTIONS — открытые вопросы и гипотезы

> Источник: PRD §16. Обновляется по мере получения ответов. Статусы: `open` / `in-progress` / `answered` / `invalidated`.

| # | Вопрос / Гипотеза | Owner | Дедлайн / Фаза | Статус |
|---|---|---|---|---|
| 1 | **Phase 0 / H1–H5:** Клиенты готовы дать API-доступ (H1); готовы платить за авто-имплементацию vs ручная работа (H2); агентства готовы перейти со Шпиониро/VisioBrand ради auto-fix (H3); реальный time-to-citation RU/retrieval-поверхностей на новый контент (H4); юр-готовность подписать DPA на авто-правки (H5). Go/no-go для тяжёлого auto-fix (P10). | founder + crawler-probe-specialist + compliance-152fz-specialist | P0 (нед. 0–8) | open |
| 2 | **Достоверность входных цифр.** Множители конверсии AI-трафика (4–14×, «+6 432% YoY») и доля ChatGPT 54,1% в РФ-рефералах — относиться как к ориентиру; перепроверить на собственных данных первых клиентов; не закладывать в обещания. | founder + geo-domain-expert | P5–P7 (первые данные) | open |
| 3 | **AI-Readiness Score — состав весов.** Зафиксировать так, чтобы Score коррелировал с реальной Visibility (исключить llms.txt из citation-веса; калибровать по фактическим citation-данным из probe). Текущие веса — исходный черновик geo-domain-expert. | geo-domain-expert + founder | P3 (первый Score), ревалидация P5+ | open |
| 4 | **Retrieval-механика Яндекс Нейро/Алисы.** Точная механика и time-to-citation на новый контент (RAG-цикл) — замерить технически (H4 спайк). Влияет на дизайн trial-окна и на позиционирование honest forecast. | crawler-probe-specialist | P0/H4 + P5 | open |
| 5 | **MCP-на-маркетинг-сайт (фаза C).** Реальный спрос на MCP-сервер для маркетинговых сайтов — отдельный дискавери до старта фазы C. Глобальный MCP-спрос подтверждён (97M загрузок SDK/мес), но «MCP на маркетинг-сайт» — гипотеза. | founder | Перед стартом фазы C | open |
| 6 | **Длительность trial vs наблюдаемость Visibility.** Финализировать (14 vs 21 vs 30 дней) по данным Phase 0 (H4 — time-to-citation) и первых design-партнёров. Readiness — мгновенный хук; Visibility — нужно ≥21–30 дн. | founder + geo-domain-expert | P0/H4 → P9 (billing design) | open |
| 7 | **Порог auto-apply (trust ladder).** Какие именно типы машиночитаемых правок дефолтно разрешать в авто-режим после скольких успешных approve-циклов. Текущий default: approval-gate на всё. | geo-domain-expert + cms-connector-specialist + founder | P10 (design phase) | open |
| 8 | **Конверсия воронки Tier 0 → Manual → Auto.** Целевые коэффициенты конверсии, где основной upsell в Auto track, оптимальная разница цен Manual vs Auto. Данных нет — только после P7+P9 в проде. | founder | P7+P9 → A→B gate | open |
| 9 | **Предиктивная Visibility-модель.** Порог накопленных before/after данных (из Auto track) для перехода от индустриальных бенчмарков к site-specific прогнозу. Сколько «пар» до/после нужно для статистически значимой модели. | geo-domain-expert + llm-router-specialist | Фаза B/C | open |

## Связанные артефакты

- Gate по P0: [`.planning/gates/P0-to-heavy-autofix.md`](./gates/P0-to-heavy-autofix.md) (H1–H5 формализованы как hard_thresholds)
- Gate A→B: [`.planning/gates/A-to-B.md`](./gates/A-to-B.md)
- PRD §16: [`.planning/PRD.md`](./PRD.md) (источник вопросов 1–9)
