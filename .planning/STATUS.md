<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас (2026-07-05): **P3 AI-Readiness Score реализован новой методологией** — детерминированный ScoringEngine поверх crawl_results (P2), веса от geo-domain-expert, llms.txt структурно исключён (§6.5); review APPROVE + audit tier-3 **PASS** (0 must-fix; аудитор не смог сломать llms.txt-инвариант); verify зелёный (90 тестов, cov 89.5%). Ждёт founder-ревью P3 PR. Вмёржено ранее: P2 Crawler (#4), методология ORIION ADR-0020/0021 (#2/#3), P1 Foundation. Машина ВЫКЛ. История фаз — PHASE-HISTORY.md. Пишет только memory-curator (шаг 8). -->

# STATUS — WIZOR

**Обновлено:** 2026-07-05 · сессия `oriion-methodology-integration` · @claude-opus
**Стадия:** **P3 AI-Readiness Score реализован** — детерминированный scoring поверх crawl_results (P2). geo-domain-expert задал веса (json_ld+faq топ; сумма 100), **llms.txt структурно исключён** (§6.5, 3 гварда). ScoringEngine (чистая fn) + ProjectionEngine + score_results + `GET /score`. Verify зелёный (90 тестов, cov 89.5%); review **APPROVE**; auditor tier-3 **PASS** (0 must-fix — не смог сломать llms.txt-инвариант даже alias-атаками). Ждёт founder-ревью P3 PR. Вмёржено: P2 Crawler (#4), методология ORIION (#2/#3), P1.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту (нужен founder) | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | 🟢 **Реализован, ждёт гейт** (2026-06-24) | `gates/P1-foundation.md` (pending) |
| P2 — Crawler/Аудит | ✅ **Вмёржен** (PR #4, 2026-07-05) | deferred_live_gold (test-WP) |
| P3 — AI-Readiness Score | 🟢 **Реализован, ждёт PR-ревью** (2026-07-05) | P3 PR |
| P4 — LLM-router | ⏳ Pending | — |
| P5 — Probe-мониторинг | ⏳ Pending | — |
| P6 — Рекомендации/gap/патчи/forecast | ⏳ Pending | — |
| P7 — Tier 0 Instant Audit (no-auth) | ⏳ Pending | — |
| P8 — Верификация (Manual proof-loop) | ⏳ Pending | — |
| P9 — Auth/биллинг/дорожки | ⏳ Pending | — |
| P10 — Auto track (auto-fix) | ⏳ Pending (gated_by P0) | — |
| → A→B gate | ⏳ Pending | `gates/A-to-B.md` |
| Phase B / C | 🧭 Рамочно (PRD §10–11) | — |

## Текущая активная фаза

**P3 (AI-Readiness Score)** — реализован на ветке `claude/oriion-methodology-integration-o2dp8a` (kickoff→domain(weights)→engine→nits). Цикл: план (0 эскалаций) → domain-build `geo-domain-expert`/Opus (карта весов, llms.txt-исключение) → `backend-implementer` (ScoringEngine чистая fn + ProjectionEngine + score_results миграция 0003 + `GET /score`) → verify (90 тестов, cov 89.5%) → review **APPROVE** → audit tier-3 **PASS** (0 must-fix). Ключевое: **§6.5 llms.txt структурно вне Score** (engine читает только WEIGHTS; import-time guard; аудитор не сломал даже alias-атаками); детерминизм (100× тест); honest-forecast (проекция = детерминированная дельта, не гарантия). Ждёт founder-ревью P3 PR (машина ВЫКЛ). Live-gold P3 — детерминированный (не требует внешних сервисов), прогнан в тестах.

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
| 0 | **Ревью P3 PR** (AI-Readiness Score) — review APPROVE + audit PASS, verify 89.5%, llms.txt-инвариант верифицирован | P3 PR |
| 0а | (P2 вмёржен #4) Дать **test-WP URL** для живого crawl golden + ключи PageSpeed/Bing/Яндекс — снимет P2 `deferred_live_gold`; те же ключи включат реальные CWV/индексируемость в Score | `PLACEHOLDERS.md` |
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
