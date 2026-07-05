# Lens · compliance · P2 · 2026-07-05

Адверсариальный проход на compliance (152-ФЗ сквозной инвариант §6.1/6/8; read-only-track).

## Read-only-граница (§6.1) — определяющий инвариант фазы
- Deliberate-действия краулера — только GET (httpx guard структурно, тесты AC-7 зелёные). Нет CMS-write, нет API-записи на клиента.
- **Caveat:** browser-JS-egress (F1) и rdflib-remote-context (F2) — сетевой трафик мимо guard. Не показана запись на клиента, но гарантия read-only структурно неполна → AC-7 нельзя объявить полностью подтверждённым для Playwright-пути. Зафиксировано как обязательный hardening-AC.

## Multi-tenant изоляция (§6.8)
- `tenant_id` NOT NULL + index + FK CASCADE на `crawl_results` (модель + миграция 0002).
- Источник тенанта вне DTO: endpoint `request.state`, Celery-аргумент, `_load_site_url` фильтрует по tenant, `save_crawl_result` берёт tenant из вызова.
- Integration AC-5 (`tenant_id != TEST` → 0) зелёный. Cross-tenant утечки не найдено.

## ПДн-резидентность (§6.6)
- Хранится контент клиентского сайта в PG (РФ-инфра). Граница: краулимая страница может содержать ПДн — но это данные клиента в его аудите, не сбор ПДн конечных пользователей WIZOR. В пределах §6.6. Внешних (не-РФ) LLM-вызовов в P2 нет.

## Неприменимо в P2
- §6.3 auto-fix, §6.4 probe-гео, §6.5 llms.txt-в-score, §6.7 uncertainty, §6.10 FAQ-авто-применение — вне scope P2 (later phases). FAQ только детектируется (read-only).

Вывод: изоляция и ПДн — pass; read-only — pass-with-caveat (F1/F2).
</content>
