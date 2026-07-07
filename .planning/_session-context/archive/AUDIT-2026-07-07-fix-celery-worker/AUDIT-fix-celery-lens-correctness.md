# AUDIT lens · correctness (adversarial) · fix-celery-worker-registration · 2026-07-07

Линза 1/1 для hotfix (Tier 2). Адверсариальный проход по 6 обязательным векторам атаки + общая корректность фикса. Код не правился (read-only аудит).

## Объект
4 коммита на `fix/celery-worker-registration` (PR #8):
- 979741a — `include` воркера: +`wizor.crawler.tasks`, +`wizor.probe.tasks`
- 705078b — celery-сервис compose: +`WIZOR_DATABASE_URL`/`WIZOR_REDIS_URL` + `depends_on: postgres(healthy)`
- a5771c2 — `dispose_engine()` в `db/session.py` + `_run_and_dispose` в обеих задачах
- e9367d5 — Dockerfile: `playwright install --with-deps chromium`

## Вектор 1 — `include`: есть ли модули с `@celery_app.task` вне списка?
grep `@celery_app.task` по `backend/src` → ровно 3 попадания:
- `worker/tasks.py:8` → `wizor.ping` (в include)
- `crawler/tasks.py:101` → `wizor.crawl_site` (в include)
- `probe/tasks.py:262` → `wizor.run_probe_batch` (в include)

`include` в `celery_app.py:21-25` содержит ровно эти 3 модуля. Orphan-модулей с задачами нет.
`test_worker.py::test_include_registers_all_task_modules` проверяет И `conf.include` (конфиг), И `celery_app.tasks` после `import_default_modules()` (реестр) — двойная проверка, устойчивая к маскировке через прямые импорты в др. тестах.
**Вердикт вектора: closed.**

## Вектор 2 — `dispose_engine`: race при concurrent-задачах в prefork?
- Пул воркера в compose (`command`, стр. 91) не задан `--pool`/`--concurrency` → **дефолт prefork**. Prefork = N отдельных OS-процессов; у каждого свой модульный глобал `_engine`/`_sessionmaker` (нет разделяемой памяти); внутри процесса задачи исполняются строго по одной. Per-task `dispose_engine` — process-local и последовательный. **Гонки нет.**
- Порядок в `dispose_engine` корректен: захват `engine = _engine` → обнуление глобалов → `await engine.dispose()`. Полу-освобождённый движок в кеше не остаётся; следующая задача пересоздаёт движок в своём loop'е (ровно цель фикса).
- Латентный риск (F1): при явной смене на `--pool threads`/`gevent` c concurrency>1 глобалы шарятся между гринлетами → dispose одной задачи закроет движок под конкурентной. В текущей конфигурации не воспроизводится. → informational, deferred-to-AC.
**Вердикт вектора: closed (актуальная конфигурация), F1 deferred.**

## Вектор 3 — защищает ли dispose при исключении в `_run`?
`_run_and_dispose` (crawler/tasks.py:113-118, probe/tasks.py:273-278): `try: return await _run(...) finally: await dispose_engine()`. Сброс кеша выполняется и на успешном пути, и при исключении → следующая задача того же воркера всегда стартует с чистым кешем движка. Корректно.
Микро-нюанс: если сам `engine.dispose()` бросит в finally — исключение вытеснит результат/исходное исключение `_run` (задача упадёт). Редко, приемлемо, не блокер.
**Вердикт вектора: closed.**

## Вектор 4 — не ломает ли dispose FastAPI-процесс? Кто ещё зовёт?
grep `dispose_engine` по `backend` → определение в `db/session.py:47` + вызовы ТОЛЬКО в `crawler/tasks.py:118` и `probe/tasks.py:278`. FastAPI-зависимость `get_session` (session.py:65) не изменена и `dispose_engine` не зовёт. uvicorn держит один долгоживущий loop → сброс ему не нужен и не происходит. Регресс API-процесса исключён.
**Вердикт вектора: closed.**

## Вектор 5 — `playwright install --with-deps chromium`: секреты / поломка образа?
Dockerfile:20 — ставит только Chromium + OS-зависимости для него. Секретов не требует и не внедряет. Комментарий фиксирует привязку версии браузера к запину `playwright==1.56.*` в pyproject (воспроизводимость). Эффект — рост размера образа (ожидаемый для JS-рендера SPA, P2 AC-3). Функциональной поломки нет.
**Вердикт вектора: closed (bloat-only, приемлемо).**

## Вектор 6 — compose-env: просочился ли секрет в дифф?
`celery`-сервис (compose стр. 84-90): `WIZOR_DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-wizor}:${POSTGRES_PASSWORD:-wizor}@postgres:5432/${POSTGRES_DB:-wizor}`, `WIZOR_REDIS_URL: redis://redis:6379/0`. Это env-интерполяция с dev-плейсхолдером `wizor` — тот же паттерн, что у сервиса `postgres` (стр. 9-11) и `backend` (стр. 56). Хардкодженного реального секрета в диффе нет. `depends_on: postgres.condition: service_healthy` добавлен корректно (устраняет гонку старта до готовности БД).
**Вердикт вектора: closed. Инв. 9 сохранён.**

## Дополнительно — тестовое покрытие фикса
- `test_worker.py`: unit-контракт `include` (конфиг + реестр). Гардит регрессию «модуль вне include».
- `integration/test_worker_dispatch.py`: живой воркер (`start_worker`), **две** задачи подряд (регрессия loop/dispose), персист в Postgres проверяется отдельным движком (корректно — loop задач жил в потоке воркера), cleanup в finally. Использует `example.test` (RFC 2606) → wholesale-сбой краула, но штатный persist `CrawlResult` (AC-6 fault-isolation). Покрывает оба дефекта (include + dispose) одним end-to-end.
Evidence (self-run, из хендоффа): unit 182 pass/1 skip/cov 88%; integration 14/14; ruff/mypy чисто; live E2E 2 краула succeeded+persisted; CI PR #8 зелёный (backend/security/evidence). Статически подтверждён кодом.

## Итог линзы
Фикс корректен во всех 6 адверсариальных векторах для актуальной конфигурации. Блокеров/major нет. Находки F1 (латентный pool-assumption) и F2 (DRY) — informational, deferred-to-AC. **Линза корректности: PASS.**
