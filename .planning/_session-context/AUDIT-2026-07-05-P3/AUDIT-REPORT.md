# AUDIT-REPORT · P3 (AI-Readiness Score) · 2026-07-05

**Вердикт:** PASS
**Tier фазы:** 3 → линз: 3
**Линзы запущены:** корректность · security · compliance
**Аудитор:** `auditor` (Opus), шаг 7 цикла. Вход: verifier PASS.
**Scope:** `git diff origin/main...HEAD` — `scoring/*.py`, `WEIGHTS.md`, migration `0003`,
`main.py`, тесты (17 файлов, +1614 строк). Source не редактировался.

## Сводка находок

| id | линза | severity | file:line | issue | disposition |
|----|-------|----------|-----------|-------|-------------|
| C-1 | корректность | info | `scoring/router.py:77` | `load_site_url→None` даёт `site_url=""` вместо 404; практически недостижимо (гейт `load_latest_crawl` уже проверил tenant+site) | deferred-to-AC (косметика, не влияет на Score/изоляцию) |
| C-2 | корректность | info | `scoring/engine.py:84` | неизвестный вердикт → `ValueError`→500; вход P2 ограничен `Literal`, fail-fast намеренный | deferred-to-AC (маппинг в 422 при недоверенном источнике, вне scope P3) |

**Блокирующих и major-находок нет.** C-1/C-2 — информационные наблюдения, не требуют фикса
в P3.

## Invariant check (10/10) — charter §6

| inv | статус | комментарий |
|-----|--------|-------------|
| **#5 llms.txt НЕ весит** | **PASS** | **HEADLINE.** Тройная защита: структурное отсутствие в `WEIGHTS` + `EXCLUDED_FROM_SCORE` + импорт-тайм `_verify_weight_model`. Адверсариально доказано: ни один вердикт llms_txt (pass/warn/fail/deferred), ни алиасы (`llms.txt`/`LLMS_TXT`/`llmstxt`/`llms`), ни ребаланс весов до суммы 100 с инъекцией `llms_txt` — не могут повлиять на Score или пройти guard. AC-2-тест non-vacuous (строгое `>`). Сконструировать вход, где llms.txt меняет Score, невозможно. |
| #2 Honest-forecast | PASS | Score детерминирован; `ProjectionEngine` — детерминированный пересчёт (`delta_score`/`new_score`), НЕ гарантия Visibility-%. WEIGHTS.md и docstrings прямо дисклеймят; внешние числа помечены «направленное свидетельство, не гарантия». Нет «гарантируем»/«100%». |
| #1 Read-only-граница | PASS | P3 — чистый compute: читает `crawl_results`, пишет только собственную `score_results`; ноль внешних API-вызовов. |
| #8 Multi-tenant изоляция | PASS | `tenant_id` из `request.state`, не из DTO; все repo-запросы tenant-scoped; integration `test_tenant_isolation_ac6` подтверждает отсутствие cross-tenant чтения. |
| #9 Secrets | PASS | Pure compute; grep диффа по секрет-паттернам чист. |
| #3 Auto-fix safety | N-A | В P3 нет autofix (P10). |
| #4 Probe-гео | N-A | В P3 нет probe (P5); ноль внешних вызовов. |
| #6 ПДн-резидентность | N-A | Scoring не обрабатывает ПДн (только вердикты факторов); резидентность — инфра P1. |
| #7 Uncertainty (N≥5+CI) | N-A | Score — детерминированная on-site метрика, не probe-Visibility; CI/шум относятся к P5. |
| #10 FAQ авто-применение | N-A | FAQ только read-only скорится как фактор; авто-применения контента нет. |

## Acceptance criteria (exit-gate P3)

| AC | статус | подтверждение |
|----|--------|---------------|
| AC-1 детерминизм | PASS | чистая функция + clock-injection + round(4); тест 100 прогонов идентичен |
| AC-2 llms.txt excluded | PASS | тройной guard + адверсариальная невозможность; тест non-vacuous |
| AC-3 компоненты раскрыты | PASS | 1 компонент/фактор в порядке WEIGHTS, все поля + `contribution==weight*value` |
| AC-4 проекция | PASS | детерминирована, вход не мутируется (copy-семантика), delta/new верны |
| AC-5 граничные значения | PASS | пусто/all-deferred→0 без div-by-zero; all-fail→0; all-pass→100 (≥85) |
| AC-6 tenant изоляция | PASS | integration-тест cross-tenant |

**Прогон тестов:** 20/20 P3 unit-тестов зелёные (`.venv/bin/pytest`). Миграционная цепочка
single-head `0001→0002→0003`; pgvector-extension в 0001.

## Fix-цикл
Не требуется (PASS без must-fix).

## Deferred findings (информационные, founder-signed не требуется)
- C-1: `site_url=""` fallback — рассмотреть 404 или пропуск, если появится путь без гейта краула.
- C-2: маппинг неизвестного вердикта в 422 — при подключении недоверенного источника входа.

## Вердикт обоснование
Все 6 AC и все применимые §6-инварианты закрыты; N-A обоснованы. Ключевой инвариант #5
(llms.txt вне Score) доказан адверсариально как структурно невозможный к нарушению — тройной
guard, причём EXCLUDED-проверка non-vacuous независимо от суммы весов. Honest-forecast (#2)
соблюдён и в коде, и в user-facing формулировках. Мультитенант, secrets, миграция, граничная
математика — чисто. Две info-находки не влияют на корректность/безопасность/комплаенс.
**→ PASS.** Handoff → `memory-curator`.
