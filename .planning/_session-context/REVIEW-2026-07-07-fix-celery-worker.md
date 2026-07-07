# Review: fix/celery-worker-registration (PR #8)

**Reviewer:** reviewer (Sonnet) · **Дата:** 2026-07-07 · **Цикл:** 1/2
**Вердикт: APPROVE**

## Объём ревью

`git diff main...HEAD` (4 коммита, 8 файлов, +150/-9):
1. `celery_app.py` — `include` расширен `wizor.crawler.tasks`, `wizor.probe.tasks`.
2. `infra/docker-compose.dev.yml` — celery-сервису `WIZOR_DATABASE_URL`/`WIZOR_REDIS_URL` + `depends_on postgres: service_healthy`.
3. `db/session.py` (`dispose_engine`) + `crawler/tasks.py`/`probe/tasks.py` (`_run_and_dispose`) — сброс кеша движка БД после каждой asyncio.run-задачи.
4. `backend/Dockerfile` — `playwright install --with-deps chromium`.
5. Тесты: `backend/tests/test_worker.py` (контракт `include`), `backend/tests/integration/test_worker_dispatch.py` (двойной диспатч через живой воркер).

## Чек-лист

**Корректность**
- Все 4 заявленных дефекта закрыты диффом 1:1; regression-тесты соответствуют каждому (include-контракт, live-dispatch/loop-leak, render в `test_crawler_render` через новый образ).
- Edge case `dispose_engine()` при `_engine is None` (первый вызов до создания движка) обработан явной проверкой — не падает.
- Race conditions: `dispose_engine` мутирует module-level `_engine`/`_sessionmaker` без блокировки, но безопасно при текущем pool-конфиге (default prefork в compose — один таск на процесс/поток последовательно). Не блокер сейчас; см. minor-finding ниже.
- Тесты покрывают happy-path (`test_include_registers_all_task_modules`) и failure-path (`test_crawl_site_dispatched_through_live_worker` — сайт не резолвится, wholesale-сбой, AC-6 fault-isolation, персист проверен отдельным движком).

**Контракты**
- API-схема не менялась (диспатч/инфра-фикс).
- `tenant_id` присутствует во всех запросах (`_load_site_url` в обеих tasks — `Site.id == site_id, Site.tenant_id == tenant_id`); интеграционный тест дополнительно проверяет `row.tenant_id == TEST_TENANT_ID` при персисте.
- TypeScript — не затронут (backend-only diff).

**Security**
- Секретов в коде нет — dev-compose credentials (`${POSTGRES_PASSWORD:-wizor}`) это существующий паттерн, уже используемый в блоке `backend`, не новый прецедент; реальные секреты — из `infra/.env` (см. шапку файла).
- Input validation — новых внешних входных точек нет.
- Read-only-граница не нарушена: crawler/probe остаются read-only; Chromium — для рендера (AC-3), не пишет наружу.
- SQL параметризован везде, включая raw `text()` в новом интеграционном тесте (`:id`-биндинги, не f-string).
- CORS не тронут.

**Качество**
- Self-audit implementer заявлен pass (182 unit/1 skip/cov 88%, 14/14 integration, ruff+format+mypy strict чисто, live E2E 2×crawl succeeded+persisted, render 7/7) — согласуется с содержанием diff.
- Dead-код/TODO без тикета — не внесено (существующий `# deferred: ... → P6` в probe/tasks.py не тронут этим диффом).
- `print()`/`console.log` с ПДн — отсутствуют.
- Diff 159 строк — декомпозиция не требуется.

## Находки

| severity(block/major/minor) | file:line | issue | required fix |
|---|---|---|---|
| minor | backend/src/wizor/db/session.py:57-62 | `dispose_engine()` мутирует module-global `_engine`/`_sessionmaker` без синхронизации; безопасно только пока celery-пул остаётся prefork/solo (по одной задаче на процесс). При будущем переключении на `--pool=threads`/`eventlet` возможна гонка (второй таск создаёт новый движок, пока первый ещё не продиспозил старый). | Не требуется сейчас; при смене пула — добавить `asyncio.Lock` или задокументировать ограничение пула явно рядом с `command` в compose/README. |
| minor | backend/src/wizor/crawler/tasks.py:113-118, probe/tasks.py:273-278 | Каждая задача теперь создаёт и полностью уничтожает engine/connection-pool (нет переиспользования пула между задачами одного воркер-процесса) — обоснованный trade-off ради корректности, но лишний connection-handshake на каждую задачу. | Не блокер; если появится нагрузка — рассмотреть per-loop engine cache вместо full dispose (не в рамках этого PR). |

Оба finding — informational/non-blocking, не требуют исправления перед мерджем.
