# HANDOFF — снапшот сессии

**Обновлено:** 2026-07-05 · `oriion-methodology-integration` · @claude-opus

## Состояние
**P3 (AI-Readiness Score) реализован** новой методологией — детерминированный scoring поверх `crawl_results` (P2, на main). Ветка `claude/oriion-methodology-integration-o2dp8a` (P3-коммиты поверх main). Ждёт founder-ревью P3 PR (машина ВЫКЛ). Вмёржено ранее в сессии: P2 Crawler (#4), методология ORIION ADR-0020/0021 (#2/#3).

## Что сделано (P3)
- **План (0 эскалаций):** 7 форков, все owned; llms.txt-исключение = граница §6.5, не форк.
- **Domain (`geo-domain-expert`/Opus):** `scoring/weights.py` — карта весов 10 факторов (сумма 100; json_ld+faq топ 16; Discovery 45/Comprehension 55), `SCORE_VERSION` 1.0.0, `normalize_verdict`, deferred исключён из числителя И знаменателя. **llms.txt структурно вне Score** (3 гварда: `EXCLUDED_FROM_SCORE` + import-time raise-guard + коммент). `WEIGHTS.md` — обоснование citation-рычагов.
- **Engine (`backend-implementer`):** `engine.py` (чистая `score_audit`), `projection.py` (`ProjectionEngine` + `Fix` P6-стаб, пересчёт без краула), `models.py` (`ScoreResultRow` TenantMixin + `Vector` UDT стаб NFR-6), миграция `0003_score_results`, `repository.py`, `router.py` (`GET /api/v1/sites/{id}/score`).
- **Гейты:** verify зелёный (ruff/mypy --strict/**90 тестов**/cov 89.5%); review **APPROVE** (llms.txt проверен структурно + не-вакуозные тесты); auditor tier-3 **PASS** (0 must-fix; пытался сломать llms.txt alias-атаками — не смог). Отчёт `_session-context/AUDIT-2026-07-05-P3/`. 2 nit'а применены (миграция заморожена литералом; тест де-тавтологизирован).

## Следующее действие
**Founder:** ревью P3 PR → мёрж. Затем **P4 (LLM-router)** — infra, не зависит от P3; ИЛИ P5 (probe, зависит P4). P3 open follow-up: реальные CWV/индексируемость факторы «оживут», когда founder даст ключи (те же, что снимают P2 deferred_live_gold).

## Read-first для следующего агента
1. `roadmap/P04-llm-router.md` (если P4) · `PLAN.md` (P3, если дорабатываем)
2. `_meta/BUILD-CHARTER.md` + `STATUS.md` + этот HANDOFF · `MEMORY-INDEX.md`
3. `.claude/autonomy/README.md` (методология)

## Escalate
Нет блокеров. Note: коммиты unsigned (нет signing-key в env — cosmetic, как #2/#3/#4). P3 live-gold детерминирован (в тестах, не deferred).
