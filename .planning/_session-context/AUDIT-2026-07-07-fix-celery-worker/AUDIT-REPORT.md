# AUDIT-REPORT · fix-celery-worker-registration (hotfix PR #8) · 2026-07-07

**Вердикт:** PASS
**Tier:** hotfix инфраструктуры воркера → трактуется как Tier 2 → 1 линза (корректность) + обязательный invariant-check 10/10
**Линзы запущены:** корректность (adversarial)
**Объект:** `git diff main...HEAD`, 4 коммита (979741a, 705078b, a5771c2, e9367d5); 8 файлов, +150/−9.

## Сводка находок

| id | линза | severity | file:line | issue | disposition |
|----|-------|----------|-----------|-------|-------------|
| F1 | корректность | minor (informational) | src/wizor/db/session.py:47 (+ crawler/tasks.py:113, probe/tasks.py:273) | `dispose_engine` над модульным глобалом безопасен только при process-local пуле (prefork/solo). При `--pool threads`/`gevent` c concurrency>1 глобалы `_engine/_sessionmaker` шарятся между гринлетами — dispose одной задачи выдернет движок из-под конкурентной. Текущий compose использует дефолтный prefork (в `command` нет `--pool`), поэтому в актуальной конфигурации дефекта НЕТ; риск латентный, гейтится будущей сменой пула. | deferred-to-AC |
| F2 | корректность | minor (informational) | src/wizor/crawler/tasks.py:113 · src/wizor/probe/tasks.py:273 | `_run_and_dispose` продублирован идентично в двух модулях (DRY-нит). Не дефект; кандидат в общий хелпер `db.session`. | deferred-to-AC |

Блокирующих и major-находок нет.

## Invariant check (10/10)
→ Проверка по `checklists/invariant-checklist.md` / charter §6. Тир hotfix — правило: любое незакрытое [ ] → минимум PASS-WITH-FIXES; инв. 1/3/9 незакрытые → BLOCKED.

| inv | статус | комментарий |
|-----|--------|-------------|
| 1 · Read-only-граница | pass | Затронуты `crawler.tasks` + `probe.tasks` — оба read-only track. Диф не добавляет write/API-вызовов к клиентским сайтам; `dispose_engine` — внутренний сброс кеша движка БД. Read-only-граница сохранена. |
| 2 · Honest forecast | pass | Не затронуто. Логика forecast/Visibility-% диффом не касается. |
| 3 · Auto-fix safety | pass | Auto-fix кода в диффе нет (P10 не тронут). N/A → не нарушено. |
| 4 · Probe-гео | pass | Geo-routing probe не изменён; добавлен только финальный `dispose_engine` в обёртке. Инвариант сохранён. |
| 5 · llms.txt вне score | pass | Scoring-логика не затронута. |
| 6 · ПДн-резидентность | pass | Celery-сервис получил `WIZOR_DATA_REGION: ru-central1` и `WIZOR_DATABASE_URL` на `postgres` (RU-стек). Резидентность сохранена/усилена. |
| 7 · Uncertainty N≥5+CI | pass | Metrics-расчёты не изменены. |
| 8 · Multi-tenant изоляция | pass | Обе задачи принимают `tenant_id`; integration-тест ассертит персист `tenant_id`. `dispose_engine` tenant-agnostic (сброс кеша движка) — cross-tenant утечки не вносит. |
| 9 · Секреты не в коде | pass | В диффе секретов нет. `WIZOR_DATABASE_URL` — интерполяция `${POSTGRES_USER:-wizor}:${POSTGRES_PASSWORD:-wizor}` с dev-плейсхолдером `wizor`, идентична паттерну сервисов `postgres` (стр. 9–10) и `backend` (стр. 56). Header compose: «Все секреты — из infra/.env (не коммитится)». |
| 10 · FAQ не авто-применяется | pass | Autofix/FAQ scope не затронут. |

**Итог инвариантов: 10/10 pass.** Инв. 1/3/9 закрыты → BLOCKED не наступает.

## Fix-цикл
Не требуется. Обе находки — informational/minor, не блокеры, disposition = deferred-to-AC.

## Deferred findings
- F1: латентный pool-assumption `dispose_engine` → AC следующей infra-фазы: «guard/документировать, что воркер запускается только под process-local пулом (prefork/solo); при переходе на threads/gevent — переработать управление жизненным циклом движка (per-task engine вместо модульного глобала)».
- F2: DRY `_run_and_dispose` → опциональный рефактор в общий хелпер.

## Вердикт обоснование
Все шесть адверсариальных векторов отработаны и закрыты: (1) `include` содержит ровно 3 модуля с `@celery_app.task` — grep подтвердил отсутствие orphan-модулей; (2) `dispose_engine` в `try/finally` — защищён при исключении в `_run`; (3) единственные вызовы `dispose_engine` — две task-обёртки, FastAPI-путь (`get_session`) его не зовёт, регресс процесса API исключён; (4) prefork = process-local глобалы, per-task dispose безопасен в актуальной конфигурации; (5) `playwright install --with-deps chromium` секретов не тащит, лишь bloat образа; (6) compose-env секрета не просачивает. Инварианты 10/10 pass. Единственные находки — латентный pool-assumption и DRY-нит, обе informational/deferred, не влияют на корректность текущей конфигурации. → **PASS**.
