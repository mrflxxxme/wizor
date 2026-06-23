# crawler-probe-specialist — memory

## Namespace

`memory/crawler-probe-specialist.md`

## MUST-persist

- **Proxy pool status**: текущие провайдеры, geo-покрытие, ротационные паттерны (без credentials — только метаданные)
- **Известные SPA-паттерны** (сайты, требующие Playwright; timeout-значения для CWV)
- **Probe-расписания**: частота по тарифу (daily/weekly/monthly)
- **Anti-patterns краулинга**: URL-паттерны исключений, infinite-scroll ловушки
- **Retry-статистика** по провайдерам (reliability score)

## MUST-NOT persist

- Proxy credentials (только в Vault/Lockbox)
- Сырые HTML-дампы страниц клиентов
- Персональные данные из ответов LLM

## Retrieval queries

- «Текущий proxy pool и geo-покрытие»
- «Известные SPA-паттерны для [домен/технология]»
- «Retry statistics для [провайдер]»

## Write triggers

- После каждого probe-батча: обновить reliability score провайдера.
- При обнаружении нового SPA-паттерна: добавить в память.
- `memory-curator` пишет после шага 8 цикла.

## Pruning

- Retry-статистика старше 30 дней → усреднить и архивировать.
