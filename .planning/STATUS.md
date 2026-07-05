<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас (2026-07-05): **P4 LLM-router реализован новой методологией** — provider-agnostic gateway, RU-default (§6.6 структурно), uncertainty (N≥5+t-interval), cost-guard, retry/fault-isolation; ключи=PLACEHOLDERS (§6.9). review CHANGES→fixed (AC-5 fault-isolation был иллюзорным — httpx→ProviderCallError) + audit tier-4 **PASS** (5 линз; §6.6 атакован 4 вектора, 0 утечек); verify зелёный (137 тестов, cov 88.8%). Ждёт founder-ревью P4 PR. Вмёржено ранее: P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1. Машина ВЫКЛ. Пишет только memory-curator (шаг 8). -->

# STATUS — WIZOR

**Обновлено:** 2026-07-05 · сессия `oriion-methodology-integration` · @claude-opus
**Стадия:** **P4 LLM-router реализован** (tier-4 infra) — provider-agnostic gateway (GigaChat/YandexGPT/vLLM/OpenAI/Perplexity), **RU-default структурно** (§6.6: ПД-задачи не уходят иностранным даже при override→downgrade), uncertainty (N≥5+t-interval, §6.7), cost-guard (§3.4), retry/fault-isolation; ключи=PLACEHOLDERS (§6.9). Verify зелёный (137 тестов, cov 88.8%); review **CHANGES→fixed** (AC-5 fault-isolation был иллюзорным: ProviderCallError не поднимался → httpx-обёртка); auditor tier-4 **PASS** (5 линз; §6.6 атакован 4 вектора → 0 утечек; секреты/probe-geo PASS). Ждёт founder-ревью P4 PR. Вмёржено: P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту (нужен founder) | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | 🟢 **Реализован, ждёт гейт** (2026-06-24) | `gates/P1-foundation.md` (pending) |
| P2 — Crawler/Аудит | ✅ **Вмёржен** (PR #4, 2026-07-05) | deferred_live_gold (test-WP) |
| P3 — AI-Readiness Score | ✅ **Вмёржен** (PR #5, 2026-07-05) | — |
| P4 — LLM-router | 🟢 **Реализован, ждёт PR-ревью** (2026-07-05) | P4 PR (deferred_live_gold) |
| P5 — Probe-мониторинг | ⏳ Pending | — |
| P6 — Рекомендации/gap/патчи/forecast | ⏳ Pending | — |
| P7 — Tier 0 Instant Audit (no-auth) | ⏳ Pending | — |
| P8 — Верификация (Manual proof-loop) | ⏳ Pending | — |
| P9 — Auth/биллинг/дорожки | ⏳ Pending | — |
| P10 — Auto track (auto-fix) | ⏳ Pending (gated_by P0) | — |
| → A→B gate | ⏳ Pending | `gates/A-to-B.md` |
| Phase B / C | 🧭 Рамочно (PRD §10–11) | — |

## Текущая активная фаза

**P4 (LLM-router)** — реализован на ветке `claude/oriion-methodology-integration-o2dp8a` (seam→domain+persistence параллельно→reconcile→fix). Цикл: план (0 эскалаций) → domain-build `llm-router-specialist`/Opus (routing/providers/uncertainty/cost-guard) ‖ `backend-implementer` (provider_configs миграция 0004 + `GET /api/v1/llm/route`) → verify (137 тестов, cov 88.8%) → review **CHANGES-REQUESTED** → fix cycle-1 → audit tier-4 **PASS** (5 линз). Ключевое: **§6.6 RU-default структурно** (ПД `content_gen/schema_gen` не уходит иностранному даже при override → downgrade к RU, `refused_override`; RU-only fallback, `NoAvailableProviderError` вместо тихого иностранного); **§6.4 probe-geo** (`assert_geo` до dispatch); **§6.9 секреты** = env/Lockbox, не в коде; uncertainty t-interval (N≥5). Review нашёл реальный баг: AC-5 fault-isolation был иллюзорным (`ProviderCallError` не поднимался) → исправлено (httpx→ProviderCallError + real-path тест). Ждёт founder-ревью P4 PR (машина ВЫКЛ). **deferred_live_gold:** живые вызовы провайдеров нужны funded-ключи + зарубежная probe-нода.

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
| 0 | **Ревью P4 PR** (LLM-router) — review CHANGES→fixed + audit tier-4 PASS, verify 88.8%; §6.6 RU-default/секреты верифицированы под атакой | P4 PR |
| 0а | Дать **funded LLM-ключи** (GigaChat/YandexGPT/OpenAI/Perplexity + vLLM-нода) — снимет P4 `deferred_live_gold`; **test-WP URL** + PageSpeed/Bing/Яндекс — снимет P2, включит CWV/индексируемость в Score | `PLACEHOLDERS.md` |
| 0б | **Ревью + (опц.) вооружение автономной машины** — `cp settings.recommended.json → .claude/settings.json` + `session-start.hook.sh → .claude/hooks/`; опц. premerge-хук + branch protection + `notify.json` | `.claude/autonomy/README.md` §Вооружение |
| 1 | **Подписать гейт P1** — CI финального коммита 76641f6 зелёный (подтверждён), 8 порогов PASS | `gates/P1-foundation.md` (`founder_signature`) |
| 2 | Принять/оспорить deferred: DLG-1 PostHog self-host (→P7), DLG-2 `make dev-bootstrap` локально (нужен Docker) | гейт P1, секция deferred_live_gold |
| 3 | Запустить P0 (Discovery) — 30 CustDev-интервью + тех-спайки (требует founder) | `roadmap/P00-discovery.md` |
| 4 | Заполнить критичные TBD-токены (Yandex Cloud, ЮKassa, LLM-ключи, юрлицо) | `PLACEHOLDERS.md` |

## Топ-риски (PRD §14)

1. **Отказ давать API-доступ** (риск №1) — митигирован: Manual track монетизирует без API (read-only-first).
2. Яндекс/Сбер запускают нативный GEO — cross-platform + CMS-moat.
3. Холодный старт без кейсов — Tier 0 + 10 design-партнёров → кейсы.
4. Скорость глобальных + капитал — скорость MVP, ревизия PRD каждые 4 нед.
5. Юр-чувствительность auto-fix — DPA/audit-log/rollback с дня 1 (P10 gated_by P0).

## Тех-снапшот

Стек залочен (ADR-0011, PRD §12). Продуктовый код: P1 (foundation) + P2 (`crawler`, миграция 0002) + P3 (`scoring`, миграция 0003, детерминированный Score). Харнесс: файл-нативный, 8 ядро + 6 профильных, тиринг по роли, **исполняемая автономия** (ADR-0021, ВЫКЛ).

## Протокол обновления

Только `memory-curator` пишет этот файл (шаг 8 цикла). История завершённых фаз → `PHASE-HISTORY.md`. Этот файл держит ТОЛЬКО rolling-состояние.
