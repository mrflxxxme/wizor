# AUDIT-REPORT · P4 (llm-router) · 2026-07-05

**Вердикт:** PASS
**Tier фазы:** 4 → линз: 5
**Линзы запущены:** корректность · security · compliance · тесты · архитектура
**Auditor:** auditor/Opus (шаг 7 цикла) · после verifier PASS

Диапазон аудита: `git diff origin/main...HEAD` — `backend/src/wizor/llm_router/*`
(config·schemas·routing·router·providers·cost_guard·uncertainty·models·repository·router_api),
миграция `0004_provider_configs`, `main.py` (+2 строки: include_router), 8 test-модулей
(46 unit-тестов + 2 integration). 2491 добавленных строк, 0 удалённых (greenfield-контекст).

---

## Сводка находок

| id | линза | severity | file:line | issue | disposition |
|----|-------|----------|-----------|-------|-------------|
| F1 | архитектура/корректность | minor | `router.py:141`, `router_api.py:127` | `provider_configs.enabled` персистится, но НЕ влияет на маршрутизацию: `preview_route` игнорирует `tenant_configs` (документировано «reserved»). Тенант-level enable/disable провайдера не исполняется в P4. | deferred-to-AC (P5/P6) |
| F2 | compliance/defense-in-depth | minor | `config.py:110` | `assert_probe_egress_foreign()`/`probe_egress_is_foreign()` определены и юнит-тестируются, но НЕ вызываются в dispatch-пути роутера. Runtime-гарантия гео держится только на `assert_geo`. Мисконфиг `probe_egress_region="ru"` не отлавливается на старте. | deferred-to-AC (P5) |
| F3 | compliance/граница | info | `routing.py:39,111` | §6.6-гарантия «ПД не уходит за рубеж» ключится на `task_type ∈ {content_gen, schema_gen}`. Если вызывающий помечает клиентские ПД как `batch` (не-ПД) с иностранным override — ПД может уйти foreign. Роутер доверяет классификации task_type (корректная слоистость: классификация — ответственность вызывающего/контракта). | observation |
| F4 | корректность | info | `router.py:170` | `cost_guard.record()` может бросить `CostBudgetExceededError` ПОСЛЕ уже выполненного вызова провайдера (деньги за этот вызов потрачены). Присуще post-hoc учёту; `pre_authorize` — форвардный предохранитель. Соответствует AC-6 (задача отменена + warning). | observation |

Ни одной находки severity `block`/`major`. F1/F2 — задокументированные reserved-швы вне
AC P4, отданы в будущие фазы под подпись founder'а. F3/F4 — корректная слоистость /
присущее свойство, действий в P4 не требуют.

---

## Invariant check (10/10 — charter §6)

| inv | статус | комментарий |
|-----|--------|-------------|
| 1 — read-only-граница | **pass** | Эндпоинты `/route`·`/providers` — GET (read-only). `upsert_provider_config` пишет ВНУТРЕННИЙ tenant-config (не внешний клиентский prod, не DPA-действие). Ни одного реального внешнего API-вызова в P4: адаптеры провайдеров срабатывают только при сконфигуренном ключе, дефолты пусты. N-A для клиентской read-only-границы. |
| 2 — honest-forecast | **pass** | Uncertainty отдаётся как диапазон `{mean, ci_lower, ci_upper, n}` (t-CI), не одно число. Нет строк «гарантируем»/«100%»/guaranteed Visibility. `_default_score` — нейтральный placeholder presence 0/1 (реальные метрики → P5). |
| 3 — auto-fix safety | **n-a** | В P4 нет autofix/авто-правок видимого контента. Не относится к фазе. |
| **4 — probe-geo** ⭐ | **pass** | `egress_for` выводит регион ИЗ провайдера (инопровайдер ⇒ `foreign`). `assert_geo` вызывается ПЕРЕД диспатчем в `complete`+`probe`; эмпирически блокирует hand-crafted RU-egress ко ВСЕМ 4 иностранным (openai/anthropic/perplexity/gemini). Probe-дефолт → openai/foreign. Роутер никогда не даёт инопровайдеру РФ-egress. Config-guard `probe_egress_region="ru"` валится (см. F2 — не в dispatch, но структурная гарантия независима). |
| 5 — llms.txt вне score | **n-a** | Scoring не затрагивается в P4. |
| **6 — ПДн-резидентность / RU-default** ⭐ | **pass** | `PD_TASK_TYPES={content_gen,schema_gen}`. `resolve_route`: иностранный override на ПД → отказ + downgrade на RU (`foreign_override_refused_pd`). `_provider_chain` для ПД-дефолта — только `RU_PROVIDERS` (gigachat→yandexgpt), НИКОГДА не содержит инопровайдера. Все RU down → `NoAvailableProviderError` (НЕ тихий foreign fallback). Эмпирически: перебор всех {ПД-task × foreign-override} → 0 утечек; с только foreign-конфигом + явным foreign override — REFUSED, инопровайдер даже не сконструирован. Adversarial-разбор ниже. |
| **7 — uncertainty (N≥5+CI)** ⭐ | **pass** | `MIN_RUNS=5`; `aggregate_uncertainty` бросает `ValueError` при N<5; probe считает CI только при `len(responses)≥5`; `n_runs=max(req.n_runs,MIN_RUNS)`. CI — реальный интервал Стьюдента `mean±t·s/√n` (таблица t df1..30, df>30→z). Ноль-дисперсия → точка (корректно). |
| 8 — multi-tenant изоляция | **pass** | `ProviderConfigRow(TenantMixin)`: `tenant_id` + index + FK CASCADE на `tenants`; unique `(tenant_id,task_type,provider)`. Repository всегда tenant-scoped; `tenant_id` — из `request.state` (§6.8), НЕ из DTO. Эндпоинты требуют `X-Tenant-Id` (иначе 400). Integration-тест доказывает cross-tenant → 0 строк. |
| **9 — secrets** ⭐ | **pass** | Все `*_api_key` дефолтят пустой строкой; ключи только из env/Lockbox (`config.py`). base_url'ы — публичные API-эндпоинты (не секреты). Bandit: **No issues / 1114 LOC**. Ключ не логируется (логи: task_type/tenant_id/provider/egress/reason). Исключения не содержат ключа (Authorization в header, не в URL). Тестовый ключ `"k"` — фикстура, не реальный секрет. |
| 10 — FAQ не авто-применяется | **n-a** | FAQ-генерация/применение → P6. Не относится к фазе. |

**Итог инвариантов:** 7 pass, 3 n-a (P4-scope), 0 fail. Все три критичных (§6.6 #6 · secrets #9 ·
read-only #1) — закрыты. Блокирующих условий system-prompt (inv 1/3/9 open) нет.

---

## ⭐ Adversarial-разбор §6.6 (compliance headline — как пытался сломать)

Цель: заставить клиентские ПД (`content_gen`/`schema_gen`) уйти к иностранному провайдеру.

1. **Tenant override = foreign на ПД-задаче.** `override=openai`, `task=content_gen` →
   `resolve_route` вернул `provider=gigachat, reason=foreign_override_refused_pd, refused_override=openai, egress=ru`. Отказ. То же для anthropic/perplexity/gemini × content_gen/schema_gen — перебор всех комбинаций дал **0 утечек** (ни provider∈FOREIGN, ни egress=foreign).
2. **Все RU down + явный foreign override.** Сконфигурирован ТОЛЬКО openai+anthropic, фабрика провайдеров бросает при любой сборке. `complete(content_gen, override=openai)` → `NoAvailableProviderError`, инопровайдер **даже не сконструирован** (фабрика не вызвана). Тихого foreign fallback нет.
3. **Hand-crafted RouteDecision.** Публичный API (`complete`/`probe`) не принимает `RouteDecision` — он всегда строится через `resolve_route` (единственный конструктор), где §6.6 закодирован структурно. Инъекция обходного решения невозможна через фасад.
4. **RU-fallback-цепочка.** `_provider_chain` для ПД-дефолта строится из `ru_default_chain()=RU_PROVIDERS` — по конструкции без инопровайдера; gigachat down → yandexgpt; оба down → явная ошибка.

**Вывод:** ПД сделать foreign не удалось ни одним вектором → §6.6 **PASS**.
Единственная теоретическая лазейка — мислейбл ПД под `batch` вызывающим (F3), но это
вне слоя роутера (доверенная классификация task_type по контракту).

---

## Deferred findings (founder-signed)

- **F1** → AC следующей фазы (P5/P6): исполнять `provider_configs.enabled` в выборе провайдера (сейчас `enabled` персистится, но роутинг ведётся только по task_type+override).
- **F2** → AC P5 (probe-контекст): вызвать `assert_probe_egress_foreign()` на старте app / в probe-dispatch как defense-in-depth к структурному `assert_geo`.

## Fix-цикл

Не потребовался — вердикт PASS без fix-loop (0 block/major находок).

## Вердикт обоснование

Все 7 AC подтверждены проходящими тестами (46 unit passed), 3 критичных инварианта
(§6.6 RU-default, secrets, read-only) закрыты — §6.6 выдержал перебор всех векторов атаки
и не пропустил ПД за рубеж; secrets чисты (bandit 0/1114 LOC, ключи из Lockbox/env).
Архитектура provider-agnostic без langchain, чистые швы, безопасная greenfield-миграция.
Найденные F1–F4 — задокументированные reserved-швы вне scope P4 и присущие свойства,
не блокирующие. **PASS.**
