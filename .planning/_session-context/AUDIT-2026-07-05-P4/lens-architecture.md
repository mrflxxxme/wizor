# Lens · Architecture · P4 (llm-router)

Adversarial-проход №5: качество provider-agnostic абстракции, vendor lock-in, швы, миграция.

## Provider-agnostic абстракция (NFR-3)
- `LLMProvider` — `runtime_checkable Protocol` (`async complete → LLMResponse`). Адаптеры:
  `_HttpProvider` (база: инъекция httpx-клиента, retry, тайминг, parse) + подклассы
  Gigachat/vLLM/OpenAI/Perplexity (OpenAI-совместимые, наследуют базовый parse) и YandexGPT
  (переопределяет endpoint/headers/payload/parse под собственный формат). Чистая расширяемость.
- **Ноль LangChain/LlamaIndex** — прямые `httpx`+`tenacity`. Vendor lock-in минимален: смена
  провайдера = новый подкласс + запись в `_OPENAI_COMPATIBLE`/фабрику. Соответствует NFR-3.
- anthropic/gemini — намеренно `UnavailableProvider` (opt-in, JIT в след. фазах), не в дефолт-
  маршрутах. Явная причина в reason, не молчаливо.

## Швы (seam cleanliness)
- Слоистость чистая: `schemas.py` (DTO/константы — единый источник провайдер-категорий) →
  `routing.py` (ЧИСТАЯ функция, без I/O/config, юнит-тестируема без сети) → `router.py`
  (оркестрация: resolve→assert_geo→pick→cost→dispatch) → `providers.py` (I/O) → `config.py`
  (Settings) → `repository.py`/`models.py` (persistence) → `router_api.py` (FastAPI).
- Границы типов: Pydantic DTO — единственный шов домен↔persistence/API (documented §7-контракт).
- `router_api._RoutingPreview` — structural Protocol + ленивый `importlib` доменного роутера:
  API не ломается при параллельной сборке (мягкий 200 resolved=false). Чистый feature-detect
  seam, точка monkeypatch в тестах. Хорошо.
- **F1 (minor):** `preview_route(tenant_configs=…)` — параметр принят, но не используется
  (reserved). Шов честно задокументирован; функциональный долг вынесен в P5/P6.

## Инъекция зависимостей / тестируемость
- `provider_factory` инъектируется в `LLMRouter` → тесты дают фейки без сети. httpx-клиент
  инъектируется в адаптер (`_owns_client` управляет закрытием) → MockTransport в retry-тестах.
  `get_llm_settings` — `lru_cache` синглтон (один разбор env/процесс). Отличная тестируемость.

## Cost-guard как per-task (не глобал)
- Свежий `CostGuard` per `complete`/`probe` — без разделяемого состояния между задачами/тенантами
  → нет cross-task/cross-tenant утечки бюджета. Числа зеркалят cost-budget.yaml §3.4 через Settings
  (единый источник). Верно.

## Миграция 0004 (безопасность)
- **Chain:** линейная 0001→0002→0003→**0004**, единственный head (`down_revision=0003_score_results`).
  Проверено — нет форка/множественных heads.
- **Greenfield:** чистый `create_table` + `create_index`, никакого ALTER существующих таблиц →
  нулевой риск для данных (контекст новый).
- **Self-contained DDL:** без импорта app-кода, без f-string DDL; стиль повторяет 0003. FK
  `ondelete=CASCADE` на `tenants.id`, unique `(tenant_id,task_type,provider)`, index по tenant_id.
- **Соответствие ORM:** миграция ↔ `ProviderConfigRow` совпадают (колонки/constraints/имена).
  `downgrade` симметричен (drop index+table). Обратима.
- `enabled` в DDL `nullable=False` без server_default — вставки идут только через repository
  (всегда задаёт enabled) → безопасно для greenfield (пустая таблица, backfill не нужен).

## main.py
- +2 строки: `from …router_api import router as llm_router` + `app.include_router(llm_router)`.
  Минимально, консистентно с crawler/scoring. Порядок middleware не затронут.

## Вердикт линзы: PASS. Абстракция provider-agnostic без langchain, швы чистые и
задокументированы, DI-тестируемость высокая, миграция 0004 безопасна (greenfield/линейная/
обратимая/self-contained). F1 — задокументированный reserved-шов, deferred.
