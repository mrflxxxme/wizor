# Lens · security · P2 · 2026-07-05

Адверсариальный проход на безопасность. Модель угроз: краулимый сайт = недоверенный вход (HTML, редиректы, JSON-LD — атакующего).

## Ключевой вопрос мандата: доверять ли `read_only_confirmed`?
**Нет, не полностью.** Guard (`ReadOnlyTransport`) структурно рвёт не-GET на уровне httpx ДО сети — это верно и покрыто тестами (`test_guard_blocks_non_get`, `reached == []`). Но `confirmed_read_only` = «ноль не-GET в guard-журнале», а журнал видит ТОЛЬКО httpx. Два пути выпускают трафик мимо:

- **F1 (major) — Playwright.** `page.goto(url, wait_until="networkidle")` исполняет JS страницы; браузер шлёт fetch/XHR/beacon (в т.ч. POST) напрямую через Chromium-стек, не через httpx-транспорт. `read_only_confirmed` вернёт `True`, хотя браузер мог сделать не-GET. Нет `page.route`-перехвата. → до fix: браузер-рендер только для доверенных/своих сайтов, либо add route-abort не-GET.
- **F2 (major) — rdflib SSRF.** `_neutralize_context` нейтрализует лишь строковый top-level `@context`. `@context: [url,...]` / dict — URL выживает → rdflib fetch remote-контекста своим загрузчиком. Атакующий сайт → `@context:["http://169.254.169.254/latest/meta-data/…"]` → SSRF/утечка cloud-creds с хоста краулера. → задать offline document-loader / отклонять remote-URL в любых формах @context.
- **F3 (minor) — SSRF через редирект.** `follow_redirects=True`, нет блока приватных диапазонов; ответ внутреннего эндпоинта осел бы в `pages_json`. Стартовый URL — свой сайт тенанта (митигирует), но редирект атакующего — нет.

## Прочее
- Secrets (§6.9): CWV/indexability — stub, ключей нет, docstring «только из окружения/Lockbox». Чисто.
- Endpoint: tenant обязателен (400 без `X-Tenant-Id`), site_id — UUID-валидация (422). Тело не принимается — минимальная поверхность.
- UA-строка идентифицирует бота — ок.

Блокеров нет; F1/F2 — обязательные hardening до production.
</content>
