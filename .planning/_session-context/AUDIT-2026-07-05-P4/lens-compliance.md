# Lens · Compliance (152-ФЗ) · P4 (llm-router)

Adversarial-проход №3: §6 инварианты 6 (ПДн-резидентность / RU-default) и 4 (probe-geo).

## §6.6 — RU-default (headline) — как пытался пробить
Векторы атаки и результат (полный разбор — в AUDIT-REPORT §Adversarial):
1. `override=foreign` × ПД-task (все 8 комбинаций openai/anthropic/perplexity/gemini ×
   content_gen/schema_gen) → **0 утечек**; каждый → downgrade на gigachat,
   `reason=foreign_override_refused_pd`, `refused_override` зафиксирован, egress=ru.
2. Все RU down + сконфигурен только foreign + явный foreign override → `NoAvailableProviderError`;
   инопровайдер **не сконструирован** (фабрика не вызвана). Нет тихого foreign fallback.
3. Hand-crafted `RouteDecision` — недостижим: фасад строит решение только через `resolve_route`
   (единственный конструктор с §6.6-логикой).
4. RU-fallback-цепочка `ru_default_chain()=RU_PROVIDERS` — структурно без инопровайдера.

Механика enforcement (структурная, не комментарий):
- `PD_TASK_TYPES=frozenset({content_gen,schema_gen})` — единственный источник ПД-классификации.
- `resolve_route`: `if contains_pd and override in FOREIGN_PROVIDERS: return _decide(default_ru…)`.
- `_provider_chain`: для `reason∈{default,foreign_override_refused_pd} and contains_pd` —
  цепочка строго из RU-провайдеров.
- `_pick_available`: перебор только по этой цепочке; пусто → `NoAvailableProviderError`.

**Результат: §6.6 PASS.** ПД клиента не выводятся foreign ни одним вектором через фасад.

### Граница (F3, info)
Гарантия ключится на `task_type`. Мислейбл клиентских ПД под `batch` (не-ПД) вызывающим →
override foreign отработает (batch — opt-in разрешён). Это корректная слоистость: классификация
task_type — ответственность вызывающего/контракта llm-router, не роутера. Задокументировать в
контракте как доверенную границу; в P5/P6 (probe/FAQ-gen — фактические вызыватели) закрепить,
что клиентский контент помечается content_gen/schema_gen.

### OSS/vLLM на ПД
`override=vllm` на content_gen honored → egress=ru (vllm∉FOREIGN). vLLM — self-hosted RU-нода;
ПД остаются в РФ → §6.6 не нарушен (residency сохранена). Приемлемо.

## §6.4 — probe-geo (NFR-2)
- `egress_for(provider)`: инопровайдер ⇒ `foreign`, RU/OSS ⇒ `ru`. Egress выводится ИЗ
  провайдера, не задаётся отдельно → рассинхрон невозможен внутри `_decide`.
- `assert_geo` вызывается ПЕРЕД диспатчем в `complete` И `probe`. Эмпирически: hand-crafted
  `RouteDecision(provider=<foreign>, egress=ru)` → `ProbeGeoViolationError` для всех 4 foreign.
  «Ноль РФ-IP к ChatGPT/Perplexity» нельзя нарушить конструктивно.
- probe-дефолт → openai/foreign; override на другой foreign остаётся foreign; override на RU
  (gigachat) → egress=ru, легитимно (опрос RU-модели о бренде — §6.4 бьёт лишь ин-модели).
- **F2 (minor):** config-guard `assert_probe_egress_foreign()` (валит `probe_egress_region="ru"`)
  определён+тестирован, но НЕ вызван в dispatch. Runtime-гарантия держится на `assert_geo`
  (структурно достаточно для «foreign не с ru-egress»). Выбор конкретной зарубежной ноды/региона —
  ответственность probe-контекста (P5) по контракту. Deferred P5: вызвать guard на старте.

## §6.8 — резидентность конфигов
`provider_configs` — в основной РФ-БД (Yandex Cloud), tenant_id+FK+unique, tenant-scoped
repository. ПД клиента как таковых не хранит (только routing-оверрайды).

## Вердикт линзы: PASS. §6.6 выдержал полный перебор атак; §6.4 структурно неразрушим.
F2 minor (defense-in-depth, deferred P5), F3 info (граница слоя).
