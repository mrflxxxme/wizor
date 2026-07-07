# HANDOFF — снапшот сессии

**Обновлено:** 2026-07-07 · `grill-tech-docs-interview` · @claude-fable

## Состояние
**Уточнение технической документации по итогам grill-интервью founder'а** (11 развязок) — цель: сделать спецификацию необходимо достаточной для автономного исполнения P6–P10 ИИ-агентами. Продуктовый код не трогался; P5 (Probe) уже вмёржен (PR #7 + hotfix #8). Ветка `claude/grill-tech-docs-interview-s9oqt4`.

## Что сделано (документация + вооружение)
- **7 новых ADR (0022–0028):** live-gold mock/live-классы AC (0022) · дефолты P9/P10 trial 14/30 + trust-ladder + Manual=Auto (0023) · prompt-set авто-ген из crawl (0024) · async Tier-0 job-модель (0025) · frontend UI-SPEC + per-phase AC (0026) · P6.5 prod-деплой (0027) · golden e2e = DoD MVP (0028).
- **Новая фаза P6.5 Production deploy** (`roadmap/P065-production-deploy.md` + `gates/P065-production-deploy.md`, schema-conformant): YC IaC + домен + TLS + CD + observability + бэкапы; параллельно P6; P7 зависит.
- **`UI-SPEC.md`** (23.9 KB, 16 экранов): инвентарь + состав + навигация + компонентная база + соответствие фазам. Honest-forecast enforced в UI.
- **Phase-спеки P6–P10 переписаны:** классы AC [mock-verifiable]/[live-only]; frontend-scope + frontend-AC; P6 +PromptSetGenerator +кабинет; P7 async +depends P6.5; P8 тренды/алерты UI; P9 дефолты +prompt-editor; P10 approve/FAQ-review/rollback/DPA UI.
- **Governance:** charter v1.5 (+7 decision-log строк, роадмап +P6.5, §12 mock/live) · ROADMAP v1.1 · ADR-индекс (28) · MEMORY-INDEX (+8 тегов) · A→B gate (+D8 +H_golden_e2e) · OPEN-QUESTIONS §6/7/8→in-progress.
- **Машина вооружена:** `.claude/settings.json` (allowlist + deny секретов) + `.claude/hooks/session-start.sh` + premerge tripwire-хук (PreToolUse). Проверено: premerge fast-path exit 0 на не-merge, PyYAML 6.0.1 в env.

## Следующее действие
**Founder:** (1) подписать гейт P1 (`gates/P1-foundation.md`); (2) настроить branch protection на main (GitHub-admin); (3) дать live-gold-набор до P7 (test-WP + funded-ключи + egress-нода + PostHog + ЮKassa sandbox); (4) вести P0 параллельно. **Затем автономно:** P6 (Рекомендации+PromptSetGen+кабинет) ‖ P6.5 (prod-деплой).

## Deferred (не блок)
- Branch protection — founder GitHub-action (Claude не self-install'ит execution-authority, ADR-0021).
- Live-only AC каскада P6–P10 — blocked_pending_resource до founder-ресурса (ADR-0022), не тихий deferred.
- Дефолты ADR-0023 — `revisit_after` P0/первые прод-данные.

## Read-first для следующего агента
1. `roadmap/P06-recommendations.md` (если P6) · `_meta/BUILD-CHARTER.md` (v1.5) + `STATUS.md` + этот HANDOFF
2. `MEMORY-INDEX.md` (recall) · `UI-SPEC.md` (frontend) · ADR-0022–0028 · `.claude/autonomy/README.md` (машина вооружена)

## Escalate
Нет блокеров. Коммиты unsigned (нет GPG — cosmetic). Live-only AC явно blocked, не тихо.
