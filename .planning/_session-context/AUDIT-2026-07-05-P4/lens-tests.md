# Lens · Tests · P4 (llm-router)

Adversarial-проход №4: не вакуумны ли AC-тесты, покрыты ли security-критичные пути.

## Прогон
`46 unit passed in 0.61s` (test_llm_routing/probe_geo/retry/cost_guard/uncertainty/endpoint,
`-m "not integration"`). 2 integration (`test_provider_configs`) требуют PG — помечены
`pytest.mark.integration`, зеркалят P3 (upsert-идемпотентность + cross-tenant), корректны по
чтению кода (setup/teardown с bind-параметрами, каскадная очистка чужого тенанта).

## Не-вакуумность AC (проверка «тест реально что-то утверждает»)
- **AC-1** `test_content_gen_defaults_to_ru_gigachat`: `spy.requested==["gigachat"]` —
  проверяет ФАКТ запрошенного провайдера, не только resp.provider. Не вакуумно.
- **AC-2** двусторонне: `foreign_optin_on_non_pd_batch_honored` (openai реально зовётся) +
  `content_gen_never_calls_foreign_without_override` (all p∉foreign) +
  `foreign_override_on_content_gen_pd_refused_and_downgraded` («openai» not in requested).
  Обе половины AC-2 закрыты.
- **AC-3** `batch_defaults_to_vllm`.
- **AC-4** `router_probe_uses_foreign_provider`: `all(p in FOREIGN_PROVIDERS)` +
  `"gigachat"/"yandexgpt" not in requested`. Плюс структурный `assert_geo` reject-тест на
  hand-crafted RU-egress (security-критичный путь geo-guard — покрыт).
- **AC-5** retry на РЕАЛЬНОМ адаптере + MockTransport (5xx/timeout/4xx/исчерпание) +
  fault-isolation (`calls==5, responses==3`).
- **AC-6** pre/record + роутер-интеграция (complete cancel, probe остановка прогонов).
- **AC-7** ручная сверка t-CI формулы + N<5 raise + MIN_RUNS==5 + роутер отдаёт uncertainty
  при 5 успешных.

## Security-критичные пути — покрытие
- **Routing refusal (§6.6):** `test_no_silent_foreign_fallback_when_all_ru_down` →
  `NoAvailableProviderError` + `spy.requested==[]` (инопровайдер не запрошен). Покрыт.
- **Geo-guard (§6.4):** `test_assert_geo_rejects_ru_egress_to_foreign_provider` +
  `test_probe_to_ru_model_uses_ru_egress_legitimately`. Покрыт.
- **Refused-override след:** `test_resolve_route_marks_refused_foreign_override_on_pd`
  (refused_override/reason/egress/contains_pd). Покрыт.
- **Tenant-изоляция:** integration `test_tenant_isolation_provider_configs` (3 проверки).
- **400 без тенанта / 422 мусор task_type:** endpoint-тесты. Покрыты.

## Пробелы (наблюдения, не блок)
- Enable/disable провайдера (`provider_configs.enabled`) в роутинге НЕ тестируется — потому что
  НЕ реализовано (F1). Латентно для P5/P6.
- config-guard `assert_probe_egress_foreign` тестируется, но интеграции «guard вызван на старте»
  нет — т.к. не вызывается (F2).
- Нет теста «override=vllm на content_gen остаётся ru» (граница OSS-на-ПД) — поведение корректно
  по коду, но явного теста нет. Nice-to-have, не блок.

## Вердикт линзы: PASS. AC-тесты не вакуумны (проверяют факт запрошенного провайдера, не только
возврат), security-критичные пути (refusal, geo-guard, tenant-изоляция) покрыты.
