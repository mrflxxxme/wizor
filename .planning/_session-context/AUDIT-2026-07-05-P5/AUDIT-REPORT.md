# AUDIT-REPORT · P5 (Probe-мониторинг) · 2026-07-05

**Вердикт:** PASS-WITH-FIXES
**Tier фазы:** 3 → линз: 3
**Линзы запущены:** корректность · security · compliance
**Scope:** `backend/src/wizor/probe/*`, `backend/src/wizor/metrics/*`, migration `0005_probe_metrics`, `main.py`, tests (P5-diff: 22 файла, +2426/-1).
**Verify-статус:** 38 P5 unit-тестов зелёные (`.venv/bin/python -m pytest tests/test_probe_geo.py test_probe_runner.py test_probe_batch.py test_metrics_engine.py test_visibility_endpoint.py` → `38 passed`). Integration-тесты (`integration/test_probe_metrics.py`) требуют реального PG — `deferred_live_gold` для probe-сети (нет фондированных ключей + зарубежной ноды), объявлено честно, не фейкается.

## Сводка находок

| id | линза | severity | file:line | issue | disposition |
|----|-------|----------|-----------|-------|-------------|
| F1 | correctness | **major** | `probe/tasks.py:60-64,110-118` + `probe/runner.py:148-163` | Per-site `brand_terms` НЕ проброшены через Celery-батч. `_ProbeRunnerSeam.run_prompt` и `collect_probe_runs` не передают `brand_terms`; раннер падает на дефолт `ProbeSettings.brand_terms()` = пусто → `detect_mention_citation` всегда `(False,False)` → в проде каждый сайт получает coverage=sov=citation=0, stability=1.0 → фиксированный `visibility_score ≈ 15.0`. Тесты маскируют явной передачей `brand_terms=[...]` / хардкодом `mentioned=True`. НЕ нарушает §6 (honest-forecast сохранён — метрика занижается, не завышается), но обесценивает фичу в проде; глобальный env-терм к тому же не tenant-safe. | deferred-to-AC |
| F2 | compliance | minor | `metrics/engine.py:155` + `metrics/schemas.py:15-16` | SoV-fallback (`sov = coverage` при отсутствии конкурент-данных) не помечен в API-контракте: ответ отдаёт `sov` обычным числом, равным coverage, с описанием «доля vs конкуренты». Потребитель не отличит proxy-SoV от настоящего. Честность не нарушена (значение не раздуто, задокументировано в докстринге движка), но задача требовала «SoV-without-competitors honestly labeled». | deferred-to-AC |
| F3 | correctness | minor | `probe/runner.py:177-206` | `_one_run` ловит только `ProbeGeoViolationError`/`ProviderError`; не-таксономная ошибка (напр. кривой proxy-URL на конструкции `httpx.AsyncClient(proxy=...)`) пробьёт `run_prompt` вопреки докстрингу «НЕ бросает». Батч-изоляция всё равно держится: `collect_probe_runs` оборачивает `run_prompt` в `except Exception` → синтетические error-runs (AC-6). Дефект только в контракте раннер-юнита. | deferred-to-AC |
| F4 | security | info | `probe/repository.py:90-121` + `metrics/router_api.py:107-136` | Принадлежность `site_id` тенанту не валидируется: можно создать `prompt_set(my_tenant, foreign_site_id)`. Строка остаётся партиционирована под тенант вызывающего → cross-tenant READ невозможен (§6.8 не нарушен); RLS отложен в P9. | info |
| F5 | compliance | info | `probe/models.py:64` + `probe/tasks.py:188` | `raw_response` (вывод LLM) хранится в RU-резидентном PG (`data_region=ru-central1`, валидируется в `core/config.py`). Промпты — бренд/рыночные запросы, ПД конечных пользователей не собираются; иностранные модели получают PD-free промпт через зарубежный прокси. Латентный риск только при инъекции PII в кастомный промпт (генерация промптов контролируется платформой). | info |

## Invariant check (10/10)

| inv | статус | комментарий |
|-----|--------|-------------|
| 1 · read-only-граница | **pass** | Probe — read-only исходящий (LLM completions); в клиентскую собственность ноль записей, DPA/API-гейт не в scope. Единственные записи — собственные таблицы WIZOR (`probe_runs`/`prompt_sets`/`visibility_metrics`). |
| 2 · honest-forecast | **pass** | Нет `гарантируем`/`100%`; всегда CI-полоса; score клампится [0..100]; пустой вход → 0; SoV-proxy задокументирован (см. F2 minor — метка в API). |
| 3 · auto-fix safety | **n-a** | В P5 автофикса нет. |
| 4 · **probe-гео** | **pass** | Структурное enforcement; адверсариально сломать не удалось (детали ниже). |
| 5 · llms.txt | **n-a** | Композит Visibility не содержит веса llms.txt; scoring llms.txt — контекст `scoring`, не тронут. |
| 6 · **ПДн-резидентность** | **pass** | RU-PG (ru-central1 валидируется); ПД конечных пользователей не собираются; RU-модели дефолт; иностранные получают PD-free промпт (F5 info). |
| 7 · **uncertainty** | **pass** | N≥5 приколочен (`max(n_runs, MIN_RUNS)`); t-интервал Стьюдента реальный; N<5 → полоса схлопывается в точку, `n` несёт правду; error-прогоны исключены из основы. |
| 8 · multi-tenant | **pass** | 3 таблицы tenant-scoped (`TenantMixin`+FK+index); `tenant_id` из `request.state`/аргумента задачи, НЕ из тела; integration-тест доказывает изоляцию (F4 info — валидация владения site). |
| 9 · secrets | **pass** | Прокси/ключи только из env/Lockbox; дефолты пустые; в diff нет хардкод-секретов (тестовые `"k"` — не секреты). |
| 10 · FAQ | **n-a** | В P5 автоприменения FAQ нет. |

**Инварианты 1/3/9 (BLOCKED-триггеры) — чисты.** Ни одного незакрытого блокирующего инварианта.

## #4 probe-гео — как пытался сломать (адверсариально)

Пробовал каждый путь пронести probe к ChatGPT/Perplexity с РФ-egress или без зарубежной ноды:

1. **Инъекция ru-egress иностранной модели.** Раннер НЕ принимает egress снаружи — `run_prompt` вычисляет `egress = egress_for_model(model)` внутри (`runner.py:168`), `_PromptCtx` frozen. Вызывающий физически не может подсунуть egress. `assert_probe_geo(chatgpt,"ru",…)` → `ProbeGeoViolationError` (`geo.py:78`). ✗ сломать не удалось.
2. **Нет прокси → форс foreign.** `assert_probe_geo(…, foreign_proxy_configured=False)` рвёт (`geo.py:85`); раннер отдаёт error-run с `egress='foreign'`, диспатча нет, RU-fallback нет. `test_foreign_model_without_proxy_is_refused_never_dispatched` подтверждает `factory.calls == []`. ✗.
3. **Обход assert → фабрика клиента.** Второй эшелон: `_default_client_factory` при foreign без прокси сам бросает `ProbeGeoViolationError` (`runner.py:99-102`) — сетевой клиент не строится. ✗.
4. **Celery-батч.** `collect_probe_runs` на wholesale-сбое ставит `egress=_egress_for(model)` = `'foreign'` для иностранных даже на синтетических error-runs (`tasks.py:128`); `PROBE_MODELS` выведены из констант `FOREIGN_MODELS/RU_MODELS`. Никогда `'ru'` для ChatGPT/Perplexity. `test_one_provider_fails_others_survive_ac6` подтверждает. ✗.
5. **Fallback-путь.** Раннер зовёт `make_provider(provider_for_model(model))` НАПРЯМУЮ, а не RU-fallback-цепочку роутера P4 — значит RU-fallback для иностранной модели структурно недостижим. ✗.
6. **egress model-derived, не injectable** — подтверждено (п.1). `provider_for_model` жёстко: chatgpt→openai, perplexity→perplexity (иностранные провайдеры); `test_foreign_models_map_to_foreign_providers`. ✗.

**Итог #4: PASS.** Не смог сконструировать путь, где foreign-probe уходит с ru или без зарубежного прокси. Enforcement структурный, в единой точке истины, дрейф невозможен.

## #7/#2 honest-forecast — результат

- **N≥5 приколочен:** `runner.run_prompt` → `n = max(n_runs, MIN_RUNS)` (5). `aggregate_uncertainty` бросает ValueError при N<5, но движок гардит `if n < MIN_RUNS: return point` (`engine.py:131`) → честный коллапс, не исключение.
- **CI реальный:** двусторонний t-интервал Стьюдента (`_T_CRIT_95` df 1..30, при df>30 нормальная аппрокс); s=0 → полоса = точка. Не выдуманное число.
- **Коллапс честный:** N<5 → `ci_lower==ci_upper==score`, `n` несёт правду; пустой вход → всё 0.
- **Visibility не гарантия:** нет `100%`/`гарантируем`; полоса шума всегда в ответе; score∈[0..100].
- **SoV-без-конкурентов:** proxy `sov=coverage` задокументирован в движке и НЕ выдаётся за конкурентную долю в коде — но в API-поверхности не помечен (F2 minor).

**Итог #7/#2: PASS** (с minor F2 на явную метку proxy-SoV).

## Deferred findings (founder-signed)

- **F1** (major): пробросить per-site `brand_terms` из crawler-сущностей через `run_probe_batch` → `_ProbeRunnerSeam.run_prompt` → `ProbeRunner`. Без этого прод-метрики бренд-агностичны (все сайты ≈15.0). → AC следующей фазы (P6-wiring или P5 follow-up).
- **F2** (minor): добавить явную метку/флаг proxy-SoV (напр. `sov_is_proxy` / признак наличия конкурент-данных) когда придёт трекинг конкурентов. → AC.
- **F3** (minor): расширить перехват в `_one_run` или валидировать proxy-URL, чтобы раннер-юнит держал контракт «НЕ бросает». → AC / hardening.
- **F4** (info): валидация принадлежности `site_id` тенанту (или RLS в P9). → P9.

## Вердикт обоснование

Все 10 §6-инвариантов закрыты; блокирующие 1/3/9 чисты; #4 probe-гео структурно неломаем (проверено 6 адверсариальными путями), #7/#2 honest-forecast честны (N≥5 приколот, t-CI реальный, честный коллапс). Вердикт **PASS-WITH-FIXES** из-за F1 (major функциональный gap: per-site brand_terms не проброшены в батч — не нарушает инвариант, но обесценивает прод-метрики) + F2 (minor: proxy-SoV не помечен в API). Обе находки — deferred-to-AC (кросс-фазовая проводка / поздний конкурент-трекинг), фаза-гейты P5 (использующие явные brand_terms/моки) зелёные. Не BLOCKED: ни одного нарушения стоячего инварианта.
