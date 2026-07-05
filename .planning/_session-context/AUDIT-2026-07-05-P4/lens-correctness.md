# Lens · Correctness · P4 (llm-router)

Adversarial-проход №1: делает ли роутер ровно то, что заявлено в AC-1..7 и docstring'ах.

## Routing-таблица (AC-1/2/3)
- `_DEFAULT_ROUTES` покрывает все 4 `TaskType`: content_gen→gigachat, schema_gen→gigachat,
  batch→vllm, probe→openai. Полное покрытие Literal — нет KeyError-путей.
- `resolve_route` — чистая функция (без I/O/config), детерминирована; порядок правил:
  probe → foreign-override-on-PD refuse → override honored → default. Разобран построчно,
  логических дыр не найдено. Эмпирически: `test_llm_routing.py` (12 тестов) + прямой перебор.

## Retry (AC-5)
- `_is_transient`: `TimeoutException|TransportError` → retry; `HTTPStatusError` ретраится
  ТОЛЬКО при `status>=500`; всё прочее (4xx) — нет. `stop_after_attempt(3)`,
  `wait_exponential`, `reraise=True`. Подтверждено: 5xx→успех на 3-й (calls==3), timeout→успех,
  4xx→1 попытка (не ретраится), 500-исчерпание→reraise на 3-й. Тесты на РЕАЛЬНОМ адаптере
  с `httpx.MockTransport` — не вакуумно.
- `perf_counter` сбрасывается в начале `_complete_with_retry`, декоратор переисполняет метод
  → latency замеряет успешную попытку. Корректно.

## Fault-isolation (AC-5)
- `probe`: `ProviderError` одного прогона логируется и `continue` — батч не падает.
  `_FlakyProvider(fail_on={1,3})` × 5 прогонов → 5 попыток, 3 успешных, uncertainty=None
  (успешных<5). Корректная деградация честности.

## Cost-guard (AC-6)
- `pre_authorize`: projected>hard → raise ДО вызова (hard-cancel forward). projected>soft →
  warning, продолжение. `record`: аккумулирует факт; >hard → raise. Подтверждено unit
  (pre>hard cancels, record accumulates+breaches) и на роутере (complete cancels on 5.0;
  probe останавливает прогоны при исчерпании — 1 из 5).
- **F4 (info):** `record` бросает ПОСЛЕ уже сделанного вызова — деньги за него потрачены.
  Присуще post-hoc учёту; `pre_authorize` — форвардный барьер; соответствует AC-6.

## preview_route seam (AC-1/2)
- Async, делегирует `resolve_route` с пустым prompt, возвращает `decision.provider`.
- **F1 (minor):** `tenant_configs` игнорируется (документировано «reserved под tenant-level
  enable/disable»). => `provider_configs.enabled` не влияет на выбор провайдера в P4.
  Ни один AC P4 этого не требует (AC-2 — про override, не про enable-флаг). Deferred P5/P6.

## Uncertainty (AC-7)
- `mean±t·s/√n`; t-таблица df1..30, df>30→z (NormalDist). Ноль-дисперсия→точка. Формула
  сверена вручную в тесте (`_T_CRIT_DF4_95=2.776`) с `rel=1e-3`. n_runs=max(req.n_runs,5).

## Вердикт линзы: PASS (F1 minor→deferred, F4 info). Тесты не вакуумны: 46 passed.
