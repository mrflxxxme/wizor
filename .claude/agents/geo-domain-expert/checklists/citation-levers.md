# citation-levers — self-audit (geo-domain-expert, P3/P6)

## Score-инварианты
- [ ] `llms.txt` НЕ в citation-весе (только Integration layer)
- [ ] Score воспроизводим; компоненты раскрыты пользователю

## Comprehension (primary levers)
- [ ] FAQPage JSON-LD + answer-first блоки 50–150 слов
- [ ] Organization/Article/Product JSON-LD с `@id`; entity-граф
- [ ] h1 единственный; h2→h3 иерархична; semantic tags

## Discovery
- [ ] robots.txt: GPTBot / PerplexityBot / YandexBot / Bingbot
- [ ] sitemap.xml валиден; IndexNow настроен; CWV LCP < 2.5s

## Честный прогноз
- [ ] Нет гарантированного Visibility-% (диапазон + доверие)
- [ ] Competitive gap = структурные разрывы, без выдуманных %
- [ ] FAQ LLM-драфты помечены `draft: true`

## Патчи
- [ ] JSON-LD прошёл rdflib-валидацию
- [ ] Видимый контент (FAQ) НЕ помечен auto-apply
