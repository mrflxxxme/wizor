# AUDIT-REPORT · P2 (crawler-audit) · 2026-07-05

**Вердикт:** PASS-WITH-FIXES
**Tier фазы:** 3 → линз: 3
**Линзы запущены:** корректность · security · compliance
**Scope:** `git diff b9ff72e...HEAD` — `backend/src/wizor/crawler/*`, `migrations/versions/0002_crawl_results.py`, `main.py`, тесты (21 файл, +1933).

---

## Сводка находок

| id | линза | severity | file:line | issue | disposition |
|----|-------|----------|-----------|-------|-------------|
| F1 | security · compliance | **major** | `crawler/fetch.py:68-87`, `crawler/guard.py:8-11,56-58` | **Playwright обходит ReadOnlyGuard.** `render_with_playwright` гонит headless-Chromium с `wait_until="networkidle"`, исполняя JS страницы. Любые fetch/XHR/beacon (в т.ч. POST) из браузера идут мимо httpx-транспорта → мимо guard. `read_only_confirmed` может вернуть `True`, хотя браузер выпустил не-GET. Guard-docstring («единственный источник истины», «structural guarantee») переоценивает гарантию: она структурна ТОЛЬКО для httpx-пути. AC-7 («ни одного PUT/POST в логах») слеп к browser-трафику — его вообще нет в guard-журнале. | deferred-to-AC |
| F2 | security · compliance | **major** | `crawler/schema_validator.py:86-108` | **rdflib может уйти в сеть за удалённым `@context` (SSRF).** `_neutralize_context` нейтрализует только когда `@context` — строка верхнего уровня. При `@context: ["https://schema.org", {...}]` (список) или dict-контексте URL-строка выживает, и `Graph().parse(format="json-ld")` резолвит remote-контекст по сети своим загрузчиком (мимо guard). JSON-LD берётся с краулимого (потенц. вредоносного) сайта → сайт может задать `@context:["http://169.254.169.254/…"]` и спровоцировать SSRF/утечку с хоста краулера. Docstring «полностью офлайн» — переоценка (верна лишь для строкового контекста). | deferred-to-AC |
| F3 | security | **minor** | `crawler/guard.py:108-113`, `crawler/audit.py:62`, `crawler/tasks.py:60-69` | **Нет SSRF/private-IP защиты на стартовом URL и редиректах.** `follow_redirects=True`; стартовый `site_url` — из `Site.url` тенанта, без проверки на localhost/приватные диапазоны. Клиентский сайт может 302-редиректить GET на внутренний/metadata-эндпоинт; guard пропускает (это GET), а тело ответа сохраняется в `pages_json`. Read-only не нарушен, но информационная SSRF-утечка возможна. | deferred-to-AC |
| F4 | correctness | **minor** | `crawler/guard.py:8-11`, `crawler/fetch.py:1-12`, `crawler/schema_validator.py:9-12` | **Docstrings переобещают гарантию** (следствие F1/F2): «единственный источник истины», «structural guarantee», «полностью офлайн». Формулировки надо смягчить до «структурно для httpx-пути; browser/rdflib-egress — вне покрытия». Честность инварианта (§6.2 дух). | deferred-to-AC |
| F5 | tests/correctness | **minor** | `crawler/tasks.py:60-69` (cov 49 %), `crawler/repository.py` (60 %) | **Security-critical tenant-scoping без быстрого unit-теста.** `_load_site_url` фильтрует `Site.tenant_id == tenant_id` — ключ изоляции (§6.8) — но покрыт только integration-тестом (нужен live PG, маркер `integration`, в быстром гейте может не гоняться). Нужен unit: чужой tenant_id → `LookupError`. | deferred-to-AC |

Ни одна находка не является демонстрацией записи на клиентский сайт или cross-tenant утечки; все — hardening egress/SSRF и покрытие. Осознанные действия краулера (httpx GET) структурно read-only. → **PASS-WITH-FIXES**, не BLOCKED.

## Invariant check (10/10) — charter §6

| inv | статус | комментарий |
|-----|--------|-------------|
| 1 · read-only-граница | **pass-with-caveat** | httpx-путь структурно GET-only (`ReadOnlyTransport` рвёт не-GET ДО сети; тесты AC-7 зелёные). **Но** Playwright (F1) и rdflib-remote-context (F2) выпускают сетевой трафик мимо guard — `read_only_confirmed` не покрывает эти пути. Deliberate write к клиенту не показан; residual egress — до fix перед production/P5. |
| 2 · honest-forecast | **pass** | Никаких Visibility-% в P2. `deferred`-вердикт корректно ≠ `fail` (нет ложной уверенности). F4 — мелкая честность формулировок. |
| 3 · auto-fix safety | **N-A** | Автофиксов в P2 нет (→ P6/autofix). |
| 4 · probe-гео | **N-A** | LLM-probe вне scope P2 (→ P5). Ни одного запроса к ChatGPT/Perplexity. |
| 5 · llms.txt в Score | **N-A** | Скоринг в P2 отсутствует (→ P3); фактор llms.txt не считается здесь. |
| 6 · ПДн-резидентность | **pass** | Хранится контент клиентского сайта (не ПДн конечных пользователей) в том же PG (РФ-хостинг по инфре). Граница: если краулимая страница содержит ПДн, они попадут в `pages_json` — это данные клиента, не сбор ПДн конечника; в пределах §6.6. Внешних LLM-вызовов нет. |
| 7 · uncertainty (N≥5+CI) | **N-A** | Метрик Visibility в P2 нет (→ P5/metrics). |
| 8 · multi-tenant изоляция | **pass** | `tenant_id` на `crawl_results` (модель+миграция, NOT NULL, index, FK CASCADE). Источник тенанта — вне DTO: endpoint из `request.state` (`get_tenant_id`, 400 без него), Celery из аргумента, `_load_site_url` фильтрует по `tenant_id`, `save_crawl_result` берёт tenant из вызова, не из тела. Integration-тест AC-5 (`tenant_id != TEST` → 0 строк) зелёный. Замечание F5 — только про быстрое покрытие. |
| 9 · secrets не в коде | **pass** | CWV/indexability — stub-адаптеры, ключей нет; docstring явно «секреты только из окружения/Lockbox». Grep diff: ноль хардкод-секретов. UA-строка — не секрет. |
| 10 · FAQ не авто-применяется | **pass** | FAQ только детектируется (`faq_detected` сигнал/вердикт) — read-only; никакой генерации/применения контента (→ P6). |

## Fix-цикл

Все 5 находок — deferred-to-AC (не fixed-in-loop): ни одна не требует блокирующей правки внутри P2, но F1/F2 — обязательные hardening-AC ДО первого production-краула / P5.

## Deferred findings (требуют founder-подписи на гейте фазы)

- **F1** (major): route-interception на уровне Playwright (блок не-GET в браузере, напр. `page.route` → abort методов ≠ GET) ИЛИ отключить сеть-исходящее из отрендеренной страницы; расширить `read_only_confirmed`/AC-7 на browser-трафик. → AC следующей итерации crawler / перед P5.
- **F2** (major): нейтрализовать/отклонять list- и dict-`@context` с remote-URL; задать rdflib document-loader без сети (offline). → AC hardening schema-validator.
- **F3** (minor): allowlist схем + блок приватных диапазонов (RFC1918/loopback/link-local 169.254.0.0/16) для стартового URL и после редиректов; лимит числа редиректов. → AC hardening fetch.
- **F4** (minor): смягчить docstrings guard/fetch/schema_validator под фактическое покрытие.
- **F5** (minor): unit-тест `_load_site_url` (чужой tenant → LookupError) в быстром гейте.

## Вердикт обоснование

Основной read-only-механизм (httpx `ReadOnlyTransport`) реализован структурно-корректно и покрыт тестами AC-7; multi-tenant изоляция (§6.8) сквозная и верифицирована; секретов нет; неприменимые инварианты подтверждены. Однако read-only-гарантия НЕ полна: browser-рендер (F1) и rdflib remote-context (F2) выпускают сетевой трафик мимо guard, из-за чего `read_only_confirmed` не является полным источником истины, а на adversarial-JSON-LD возможна SSRF. Демонстрации записи на клиента/утечки тенанта нет → **PASS-WITH-FIXES** с обязательными hardening-AC (F1/F2) до production-краула, а не BLOCKED.
</content>
</invoke>
