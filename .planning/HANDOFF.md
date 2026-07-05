# HANDOFF — снапшот сессии

**Обновлено:** 2026-07-05 · `oriion-methodology-integration` · @claude-opus

## Состояние
**P4 (LLM-router) реализован** новой методологией — provider-agnostic gateway (tier-4 infra). Ветка `claude/oriion-methodology-integration-o2dp8a` (P4-коммиты поверх main). Ждёт founder-ревью P4 PR (машина ВЫКЛ). Вмёржено ранее в сессии: P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3).

## Что сделано (P4)
- **План (0 эскалаций):** router-дизайн agent-owned; llm_router = tripwire `secrets_keys_crypto` (нота: ack на мёрже при вооружённой машине; сейчас founder-PR).
- **Domain (`llm-router-specialist`/Opus):** `config.py` (ключи=PLACEHOLDERS, empty→unavailable), `routing.py` (§6.6 структурно: ПД-задачи не уходят иностранному → downgrade к RU), `providers.py` (httpx-адаптеры + tenacity), `uncertainty.py` (t-interval, N≥5), `cost_guard.py`, `router.py` (LLMRouter.complete/.probe + preview_route).
- **Persistence/API (`backend-implementer`):** `provider_configs` (TenantMixin) + миграция `0004` + repository + `GET /api/v1/llm/{route,providers}`.
- **Reconcile (orchestrator):** довязал `preview_route` шов (эндпоинт↔router) + E501-фикс в seam.
- **Гейты:** verify зелёный (ruff/format/mypy/**bandit/pip-audit**/137 тестов/cov 88.8%); review **CHANGES-REQUESTED** → cycle-1 fix; auditor tier-4 **PASS** (5 линз). Отчёт `_session-context/AUDIT-2026-07-05-P4/`.
- **Реальный баг, пойман review:** AC-5 fault-isolation был иллюзорным — `ProviderCallError` определён, но не поднимался; probe (`except ProviderError`) не ловил raw httpx → persistent-сбой ронял бы батч. Фикс: httpx→ProviderCallError + real-adapter fault-isolation тест.

## Следующее действие
**Founder:** ревью P4 PR → мёрж. Затем **P5 (Probe-мониторинг**, зависит от P4 — использует LLMRouter probe-канал + dual-geo ноды). P4 deferred_live_gold: funded LLM-ключи + зарубежная probe-нода.

## Открытые (deferred, не блок)
- provider_configs.enabled персистится, но не enforced в routing (→P5/P6).
- config.assert_probe_egress_foreign() не вызван в dispatch (geo держит `assert_geo`; ноды/регион — probe P5).

## Read-first для следующего агента
1. `roadmap/P05-probe-monitoring.md` (если P5) · `_meta/BUILD-CHARTER.md` + `STATUS.md` + этот HANDOFF
2. `MEMORY-INDEX.md` (recall) · `.claude/autonomy/README.md` (методология + **урок: не спавнить PR-работу через fire_trigger-сессии**)

## Escalate
Нет блокеров. Коммиты unsigned (нет GPG-ключа в env — cosmetic, не блок CI/мёржа). P4 live-gold отложен явно.
