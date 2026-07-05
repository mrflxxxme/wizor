# Lens · Security · P4 (llm-router)

Adversarial-проход №2: SSRF, secrets, error-handling, инъекции.

## SSRF на base_url провайдеров
- `make_provider` берёт `base_url` ИСКЛЮЧИТЕЛЬНО из `settings.base_url(provider)` —
  Pydantic Settings из env/`.env`/Lockbox. **Тенант не может задать base_url:** таблица
  `provider_configs` хранит только `(tenant_id, task_type, provider, enabled)` — никакого
  URL/endpoint. `preview_route` принимает лишь `task_type`+`provider_override` (оба Literal,
  422 на мусор). => tenant-controlled base_url невозможен, SSRF-вектор через тенанта закрыт.
- Единственные URL-источники — публичные дефолты провайдеров (gigachat.devices.sberbank.ru,
  api.openai.com, …), переопределяемы только оператором через env. Приемлемо (config/env-only).

## Secrets (§6 инв. 9) — критичный
- Все `*_api_key` дефолтят `""` (config.py:40–70). Реальные значения — только env/Lockbox.
- **Bandit: No issues identified / 1114 LOC / 0 #nosec.**
- Ключ НЕ логируется: `logger.info("llm.route.selected", …)` пишет task_type/tenant_id/
  provider/egress/reason/refused_override — без ключа. cost_guard/probe-логи — без ключа.
- Ключ НЕ в исключениях: `ProviderUnavailableError`/`ProviderCallError` несут provider+reason;
  `httpx.HTTPStatusError` несёт URL (ключ в Authorization-header, не в URL) → не течёт.
  YandexGPT — `Api-Key` header, не query. Проверено grep: ни одного непустого дефолт-ключа,
  ни `sk-`/`AKIA`/hardcoded token.

## Error-handling
- `UnavailableProvider.complete` → `ProviderUnavailableError` (не сеть) при пустом ключе;
  роутер изолирует. `raise_for_status` разграничивает 4xx/5xx. Нет «глотания» исключений
  без лога: `router_api._load_router` логирует `constructor_failed` (не тихий pass).

## Инъекции / вход
- `task_type`/`provider`/`provider_override` — Pydantic `Literal` (whitelist) на границе API →
  произвольные строки отбиваются 422. `provider_configs.task_type/provider` — String(32) в БД,
  но форма валидируется DTO на входе; SQL — параметризован (SQLAlchemy core/ORM, `pg_insert`).
  Integration-тесты используют `text()` только для setup/teardown с bind-параметрами.

## multi-tenant (косвенно security)
- `tenant_id` из `request.state` (§6.8), НЕ из тела → нет tenant-spoofing через DTO.
  Cross-tenant изоляция доказана integration-тестом (0 строк под чужим фильтром).

## Вердикт линзы: PASS. Нет SSRF-вектора через тенанта, secrets чисты (bandit 0),
исключения/логи не текут ключами.
