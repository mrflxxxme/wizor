# Lens: Security · P5 · 2026-07-05

Адверсариальный проход №2 (Tier 3). Фокус: secrets (#9), multi-tenant изоляция (#8), поверхность API, инъекции.

## 1. Secrets (§6.9) — PASS

- `ProbeSettings` (`probe/config.py`): `probe_proxy_foreign`/`probe_proxy_pool`/`probe_brand_terms` — дефолт пустой, источник env/`.env`/Lockbox (`env_prefix="WIZOR_"`). Ни одного хардкод-креда.
- LLM-ключи берутся из `LLMRouterSettings` через `make_provider` (единая точка инъекции, P4) — probe их не дублирует и не логирует.
- grep diff `probe/*`+`metrics/*` по `(api_key|secret|password|token|proxy)=…["'][A-Za-z0-9]{8,}` → 0 совпадений. Тестовые `"openai_api_key":"k"` — заведомо не секреты.
- Логи: `structlog` пишет `tenant_id`/`site_id`/`model`/`prompt_id`/`run_index`/`error` — прокси-URL и ключи НЕ логируются. `probe.geo_refused`/`provider_failed` без кред. ✔

**Итог #9: PASS.**

## 2. Multi-tenant изоляция (§6.8, #8) — PASS

- Все 3 таблицы несут `tenant_id` через `TenantMixin` + FK `tenants.id` (`ON DELETE CASCADE`) + индекс. Миграция 0005 совпадает.
- `tenant_id` берётся ИЗ КОНТЕКСТА, не из тела:
  - эндпоинты — `_require_tenant(request)` → `get_tenant_id` из `request.state` (middleware `TenancyMiddleware`); нет `X-Tenant-Id` → 400 (`test_visibility_400_when_no_tenant`, `test_put_prompts_400_when_no_tenant`).
  - Celery — `tenant_id` аргумент задачи (парсится в UUID).
- Все запросы репозиториев фильтруют по `tenant_id` (`load_latest_visibility`, `load_active_prompt_set`, `upsert_prompt_set`, `save_*`). Записи ставят `tenant_id` из аргумента, не из DTO.
- `integration/test_probe_metrics.py::test_tenant_isolation_probe_and_metrics` доказывает: строки чужого тенанта невидимы под фильтром тестового; своя строка не видна под «не-тестовый тенант».

**Атака cross-tenant READ:** запрос `GET /sites/{foreign_site}/visibility` под своим `X-Tenant-Id` → запрос `WHERE tenant_id=mine AND site_id=foreign` → 0 строк → 404. Утечки нет. ✔

**F4 (info).** `site_id` не валидируется на принадлежность тенанту: `upsert_prompt_set` вставит `(my_tenant, foreign_site_id)` (FK требует лишь существования site где-либо). Но строка партиционирована под тенант атакующего → жертва её не читает, атакующий читает только свой тенант. §6.8 (cross-tenant READ) НЕ нарушен. RLS-политики Postgres отложены в P9 (задокументировано в `core/tenancy.py`). Ideal: составной FK `(tenant_id, site_id)` или проверка владения. Disposition: info.

**Итог #8: PASS** (F4 info).

## 3. Поверхность API

3 эндпоинта (`metrics/router_api.py`), все под `_require_tenant`:
- `GET /sites/{site_id}/visibility` — 400 без тенанта, 404 без агрегата, 422 на кривой UUID (path-валидация FastAPI), 200 форма (AC-4). Все ветки протестированы (`test_visibility_endpoint.py`).
- `GET/PUT /sites/{site_id}/prompts` — те же гейты; PUT создаёт новую версию (AC-5).
- `PUT` тело `PromptSetUpdate` — Pydantic-валидация; `prompts: list[str]`. Инъекций нет: `prompts` уходит в JSONB через ORM (параметризовано), не в raw SQL.
- Raw SQL встречается только в ТЕСТАХ (`text(f"DELETE FROM {table} …")` с `# noqa: S608`) — таблица из белого литерального кортежа, значения параметризованы. В проде raw SQL нет.

## 4. SSRF / egress-поверхность

- Probe уходит на LLM-endpoint'ы из `LLMRouterSettings.base_url(provider)` (конфиг, не пользовательский ввод) — пользователь не управляет URL назначения. Промпт-текст — тело запроса, не адрес.
- Прокси — из env-пула, ротация round-robin; пользователь не инъектит прокси. ✔
- Иностранный egress строго через зарубежный прокси (см. lens-compliance / #4). Ноль РФ-IP.

## Вывод линзы

Secrets чисты (дефолты пустые, Lockbox-путь, ноль хардкода, ключи/прокси не логируются). Multi-tenant изоляция структурна (tenant_id из контекста, фильтрация везде, integration доказывает). API-поверхность узкая, все коды ошибок покрыты, SQL параметризован, SSRF-вектора нет. Один **info** (F4 — валидация владения site, покрывается RLS P9). Блокеров нет; #8/#9 PASS.
