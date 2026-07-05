# AUDIT · P3 · линза КОРРЕКТНОСТЬ · 2026-07-05

Адверсариальный проход по детерминизму, граничной математике, проекции и миграции.
Все входы строятся из `WEIGHTS`, чтобы не хардкодить конкретные веса.

## AC-1 — Детерминизм (воспроизводимость)
- `ScoringEngine.score_audit` — чистая функция: без I/O, `calculated_at` инъектируется на
  границе (`router.py:79`), внутри движка часов нет (`engine.py:62-109`).
- Float-шум погашен `round(..., 4)` (`engine.py:40, 101, 104`).
- `index_verdicts` детерминирован относительно порядка входа (последняя запись побеждает
  при дубле фактора — `engine.py:43-56`).
- Тест `test_determinism_100_runs_identical` — 100 прогонов, `len({scores}) == 1` + полный
  `model_dump` идентичен. **PASS.**

## AC-2 — llms.txt исключён (см. lens-compliance для детальной атаки)
- Движок джойнит вход ТОЛЬКО с `WEIGHTS` (`engine.py:82`); `llms_txt` отсутствует в `WEIGHTS`
  → сигнал никогда не читается. Проверено адверсариально (pass/warn/fail/deferred + алиасы) —
  Score не сдвигается. **PASS.**

## AC-3 — Компоненты раскрыты
- Ровно один `ScoreComponent` на фактор `WEIGHTS`, в порядке `WEIGHTS` (`engine.py:82-96`),
  включая `deferred` (value 0, вклад 0) — прозрачность.
- Поля `name/layer/weight/value/verdict/contribution/description` присутствуют; инвариант
  `contribution == weight * value` проверен тестом. **PASS.**

## AC-4 — Readiness-проекция (без мутации)
- `ProjectionEngine.project`: текущий Score считается один раз; на каждый фикс — патч на
  КОПИИ (`_apply_fix` копирует `dict(entry)` per-запись, `projection.py:113-132`), исходный
  `audit_summary` неизменен (`test_projection_does_not_mutate_input`).
- `delta_score = round(new - current, 4)`, `new_score` = Score с патчем — арифметика верна
  (`test_fix_fail_to_pass_raises_score_ac4`).
- Фикс на факторе вне `WEIGHTS` (`llms_txt`) → добавляется запись, движок её игнорирует →
  `delta_score == 0` (`test_fix_on_llms_txt_has_zero_delta`). **PASS.**

## AC-5 — Граничная математика (нет деления на ноль)
- Пустой аудит → `scored_weight == 0.0` → `score = 0.0` явной веткой (`engine.py:101`),
  БЕЗ `ZeroDivisionError` (`test_empty_audit_scores_zero_ac5`, `test_all_deferred_...`).
- Все scored=fail → 0; все scored=pass → 100 (deferred/future нейтральны, не мешают ≥85) —
  `is_scored` исключает `deferred` из числителя И знаменателя (`engine.py:97-99`). **PASS.**

## Vector UDT / миграция 0003
- Цепочка ревизий чиста: `0001_initial → 0002_crawl_results → 0003_score_results`
  (single-head, без ветвлений).
- `CREATE EXTENSION IF NOT EXISTS vector` в 0001 (стр. 28) — 0003 корректно опирается на неё.
- `Vector.get_col_spec` рендерит `vector(1536)` из КОНСТАНТЫ `EMBEDDING_DIM` (int, не польз.
  вход) — не инъектируемо. `embedding` nullable, всегда NULL в P3 (стаб NFR-6).
- FK `tenant_id`/`site_id` ON DELETE CASCADE + оба индекса; `downgrade` дропает индексы+таблицу
  в обратном порядке — обратима, greenfield CREATE (безопасна). **PASS.**

## Минорные наблюдения (не блок, не требуют фикса в P3)
- **C-1 (info):** эндпоинт при `load_site_url → None` подставляет `site_url=""` вместо 404.
  Практически недостижимо: `load_latest_crawl` уже отфильтровал по (tenant, site), значит сайт
  тенанта существует. Косметика site_url, не влияет на Score/изоляцию.
- **C-2 (info):** неизвестный вердикт во входе → `ValueError` → 500 на эндпоинте. Вход из P2
  ограничен `Literal` (pass/warn/fail/deferred); fail-fast намеренный (`test_unknown_verdict_raises`).
  При будущем недоверенном источнике — маппить в 422. Вне scope P3.

**Вывод линзы: PASS.**
