# Lens: Корректность · P5 · 2026-07-05

Адверсариальный проход №1 (Tier 3). Фокус (по заданию): fault-isolation/exception-taxonomy (AC-6), детерминизм метрик, safety миграции 0005, N≥5+CI.

## 1. Exception taxonomy — ловит ли раннер то, что реально бросают P4-адаптеры?

P4 (`llm_router/providers.py`) бросает из `complete`:
- `ProviderUnavailableError(ProviderError)` — провайдер не сконфигурирован (пустой ключ) → `make_provider` возвращает `UnavailableProvider`, чей `.complete` бросает это.
- `ProviderCallError(ProviderError)` — `httpx.HTTPError` (4xx после без-ретрая / 5xx после исчерпания ретраев / таймаут/сеть) конвертируется в `_HttpProvider.complete` (`providers.py:165-166`).

Раннер `_one_run` (`runner.py:191-206`) ловит `except ProviderError` → покрывает ОБА подкласса (оба наследуют `ProviderError`). ✔ Таксономия согласована.

- `test_fault_isolation_persistent_5xx_yields_error_runs` — 5xx после ретраев → `ProviderCallError` → error-run с `"provider"`. Зелёный.
- `test_fault_isolation_unavailable_provider_yields_error_runs` — пустой ключ gigachat → `ProviderUnavailableError` → error-run. Зелёный.

**F3 (minor).** `_one_run` НЕ ловит не-таксономные исключения. Реальный вектор: `httpx.AsyncClient(proxy=proxy_url,…)` в `_default_client_factory` при кривом proxy-URL из env может бросить не-`ProviderError` → пробьёт `run_prompt` (докстринг обещает «НЕ бросает»). На уровне БАТЧА изоляция держится: `collect_probe_runs` оборачивает `run_prompt` в `except Exception` → синтетические error-runs (`tasks.py:119-133`), AC-6 не страдает. Дефект — только контракт раннер-юнита. Disposition: deferred-to-AC.

## 2. Fault isolation (AC-1/AC-6)

- Раннер: per-run сбой → error-run, батч живёт (`_error_run`, egress сохраняется). ✔
- Батч: `collect_probe_runs` — модель со 100% провалом → `failed_models` (лог `provider_failed`, `tasks.py:157-165`), НЕ `batch_failed`; остальные 3 модели успешны. `test_one_provider_fails_others_survive_ac6` + `test_batch_survives_partial_failure_yields_metrics_ac1` зелёные. ✔
- Wholesale-сбой раннера ловится `except Exception` → N синтетических error-runs с корректным `egress`. ✔

## 3. Детерминизм метрик (движок чист)

`aggregate_visibility` — чистая функция, без I/O и часов (`calculated_at` инъектируется в persistence). `test_deterministic_same_input_same_output` доказывает побайтовую воспроизводимость. Округление `_ROUND_NDIGITS=4` гасит float-шум. Группировка — `sorted(grouped.items())` (детерминированный порядок). ✔

Формула композита: веса 0.40/0.20/0.25/0.15 (сумма=1), score = 100·Σ. Компоненты клампятся [0..1] Pydantic-полями; score [0..100]. `test_aggregate_shape_ac4` подтверждает форму. ✔

Stability (AC-7): `1 − 4·p·(1−p)` — при p∈{0,1} (детерминированный mock) → 1.0>0.8. `test_stability_gt_08_on_deterministic_runs_ac7` зелёный. ✔

## 4. N≥5 + CI (AC-3, §6.7)

- N≥5 приколот дважды: `runner.run_prompt` → `max(n_runs, MIN_RUNS)`; `RUNS_PER_PROMPT=MIN_RUNS` в батче.
- `_noise_band`: N<5 → возвращает `(score,score,n)` (полоса схлопывается), N≥5 → t-интервал через `aggregate_uncertainty`. Гард `if n < MIN_RUNS` гарантирует, что `aggregate_uncertainty` (бросающая ValueError при N<5) НЕ вызывается на малой выборке. ✔
- Error-прогоны исключены из основы CI (`successes = [r for r in runs if r.error is None]`); `test_failed_runs_excluded_from_success_basis`: `n=5` при 6 прогонах (1 error). ✔

**Замечание (info):** полоса шума считается по пулу per-run сигналов `s_i=0.6·mentioned+0.4·cited` ВСЕХ промптов×моделей вместе, а margin навешивается на композит (у которого другие веса). Это эвристическая полоса, не строгий CI самого `visibility_score`. Задокументировано в докстринге движка; для §6.7 (заявлять улучшение только вне полосы) — приемлемый прокси. Не дефект.

## 5. Migration 0005 safety

- Greenfield `CREATE TABLE` ×3, стиль повторяет 0003/0004: self-contained, без импорта app-кода, без f-string DDL. `down_revision="0004_provider_configs"` — линейная цепочка. ✔
- Все FK — `ON DELETE CASCADE` на `tenants.id`/`sites.id`; индексы на `tenant_id`+`site_id`; `uq_prompt_sets_tenant_site_version` (AC-5 версионирование). ✔
- `downgrade` симметричен (drop index → drop table в обратном порядке). ✔
- Схема миграции ↔ ORM-модели совпадает (типы/nullable/constraints идентичны `probe/models.py` + `metrics/models.py`). ✔
- Не-разрушающая: только CREATE, ноль ALTER/DROP существующих объектов → безопасна для forward-migrate на непустой БД. ✔

## 6. F1 (major) — brand_terms не проброшены в батч

`collect_probe_runs` (`tasks.py:110-118`) зовёт `runner.run_prompt(prompt_id=…, prompt=…, model=…, n_runs=…)` — БЕЗ `brand_terms`. `_ProbeRunnerSeam` (`tasks.py:60-64`) вообще не объявляет `brand_terms`. `ProbeRunner.run_prompt` тогда берёт `self._settings.brand_terms()` = `_split_csv(WIZOR_PROBE_BRAND_TERMS)` = пусто по дефолту → `detect_mention_citation("…", [])` → `(False,False)` для КАЖДОГО прогона.

Следствие в проде: coverage=0, sov=0 (=coverage), citation=0, а all-False mentions → дисперсия 0 → stability=1.0 → `score = 100·0.15 = 15.0` фиксированно для любого сайта. Юнит-тесты это МАСКИРУЮТ: `test_probe_runner` передаёт `brand_terms=[...]` явно; `_FakeRunner` в `test_probe_batch` хардкодит `mentioned=True/cited=True`. Итог — прод-путь бренд-агностичен.

Не нарушает §6 (honest-forecast цел — метрика ЗАНИЖАЕТСЯ, не завышается). Глобальный env-терм к тому же не tenant-safe (один бренд на всех тенантов). Fix — пробросить per-site термы из crawler-сущностей: `run_probe_batch` → расширить seam `run_prompt(..., brand_terms=)` → раннер. Disposition: **deferred-to-AC** (кросс-фазовая проводка; фаза-гейты зелёные).

## Вывод линзы

Ядро корректно: taxonomy согласована, fault-isolation держится на обоих уровнях, движок детерминирован, N≥5+CI честны, миграция безопасна. Один **major** (F1 — brand_terms wiring) и один **minor** (F3 — контракт раннер-юнита), оба deferred-to-AC. Блокеров нет.
