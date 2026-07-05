# Lens · correctness · P2 · 2026-07-05

Адверсариальный проход на корректность.

## Проверено
- **Batch fault-isolation (AC-6):** `_crawl_pages` ловит `httpx.HTTPError` пофайлово (`continue`), per-page 4xx/5xx не бросаются (`fetch_page` кладёт статус в результат). Ссылки берутся только с 2xx. Стартовая страница недоступна → `CrawlResult.error` заполнен, `pages=[]`. Корректно.
- **SPA (AC-3):** `_looks_like_spa` эвристика → `render_with_playwright`; `rendered_via_js` выставляется только если нормализованный контент изменился. `normalize_html` выкидывает script/style, схлопывает пробелы — устойчивый `content_hash`. Корректно.
- **JSON-LD валидатор (AC-4):** синтаксис → структура (@context/@type, @graph) → rdflib. Пустой набор = вакуумно валиден. Все ошибки собираются. Корректно (кроме remote-context — см. security F2).
- **Retry:** tenacity `retry_if_exception_type(OSError)`, exp backoff, `reraise=True`. `audit_site` не бросает на per-page — ретраится лишь wholesale OSError. Разумно.
- **Async/Celery:** `asyncio.run(_run(...))` в синхронной обёртке — стандартно, свой loop на задачу.

## Находки
- **F4 (minor):** docstrings guard/fetch/schema_validator переобещают («источник истины», «structural guarantee», «полностью офлайн») — противоречит F1/F2. Смягчить.
- **F5 (minor):** `_load_site_url` (tenant-scoping) без быстрого unit-теста; cov tasks.py 49 %.

Прочее корректно. Замечаний-блокеров нет.
</content>
