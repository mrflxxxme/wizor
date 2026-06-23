# geo-domain-expert — memory

## Namespace
`memory/geo-domain-expert.md` (файл-нативный).

## MUST-persist
- Веса AI-Readiness Score (текущая версия + история ревизий с ADR-ссылкой)
- Citation-левера с актуальными impact-данными (обновляются при новых рыночных данных)
- Known-good JSON-LD шаблоны (Organization, FAQPage, Article, Product, HowTo)
- Competitive patterns: структурные паттерны цитируемых RU-LLM сайтов
- Известные ловушки: llms.txt-театр, выдуманные %, FAQ без answer-first

## MUST-NOT persist
- Реальный контент сайтов клиентов (только ссылки)
- Секреты и ключи API
- Полные HTML-дампы (только структурированные выжимки)

## Retrieval queries
- «Текущие веса Score Discovery+Comprehension»
- «Паттерны citation-левёров RU-рынок»
- «Known-good JSON-LD шаблон [тип]»

## Write triggers
После каждой P3/P6: обновить веса если изменились, добавить competitive pattern. `memory-curator` — единственный писатель.

## Pruning
Competitive patterns старше 6 мес → архивировать.
