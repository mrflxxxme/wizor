# HANDOFF — снапшот сессии

**Обновлено:** 2026-07-05 · `oriion-methodology-integration` · @claude-opus

## Состояние
**P5 (Probe-мониторинг) реализован** новой методологией — dual-geo probe 4 LLM-моделей + Visibility-метрики (tier-3, read-only). Ветка `claude/oriion-methodology-integration-o2dp8a` (P5-коммиты поверх main). Ждёт founder-ревью P5 PR (машина ВЫКЛ). Вмёржено ранее: P4 LLM-router (#6), P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1.

## Что сделано (P5)
- **Domain (`crawler-probe-specialist`):** `probe/geo.py` (§6.4 структурно: egress из модели, foreign без прокси→refused, 0 dispatch, никогда RU), `probe/runner.py` (N≥5 прогонов, proxy-rotation, retry, fault-isolation per-run→error-run), `probe/config.py` (PROXY_FOREIGN=PLACEHOLDER). Переиспользует P4 LLMRouter/uncertainty.
- **Persistence/metrics (`backend-implementer`):** probe_runs/prompt_sets/visibility_metrics (миграция 0005) + Celery `run_probe_batch` + `metrics/engine.py` (детерминир. Coverage/SoV/Citation/Stability/Visibility + CI-полоса) + `GET /api/v1/sites/{id}/visibility` + версионируемые промпты.
- **Reconcile (orchestrator):** довязал `ProbeRunner`-шов (list-returning run_prompt) task↔runner.
- **Гейты:** verify зелёный (ruff/format/mypy/bandit/pip-audit/182 теста/cov 88.2%); review **CHANGES-REQUESTED**→fix cycle-1; auditor tier-3 **PASS-WITH-FIXES**. Отчёт `_session-context/AUDIT-2026-07-05-P5/`.
- **Реальный баг, пойман review:** метрики были инертны в prod — `brand_terms` не прокидывались через batch-шов → `detect_mention_citation` всегда (False,False) → Visibility≡15.0/сайт. Фикс: per-site brand_terms из URL сайта (`_site_brand_terms`) через шов. + honest SoV (`has_competitor_data`) + broadened runner catch.

## Следующее действие
**Founder:** ревью P5 PR → мёрж. Затем **P6 (Рекомендации + competitive gap + патчи + honest forecast**, зависит от P3+P5). P5 deferred_live_gold: funded LLM-ключи + зарубежная egress-нода.

## Deferred (не блок; founder-signed на гейте)
- rich entity brand-terms (продукты/алиасы из crawler-entities) → **P6**.
- competitor SoV (реальная конкурентная доля) → **P6** (сейчас sov=coverage-прокси, помечен).
- probe_runs ↔ prompt_set_version binding → **P8** (evidence).
- site_id-ownership RLS → **P9**.

## Read-first для следующего агента
1. `roadmap/P06-recommendations.md` (если P6) · `_meta/BUILD-CHARTER.md` + `STATUS.md` + этот HANDOFF
2. `MEMORY-INDEX.md` (recall) · `.claude/autonomy/README.md` (методология + **урок: PR-работу НЕ через fire_trigger-сессии**)

## Escalate
Нет блокеров. Коммиты unsigned (нет GPG-ключа в env — cosmetic, не блок CI/мёржа; все 6 прошлых PR смёржены). P5 live-gold отложен явно.
