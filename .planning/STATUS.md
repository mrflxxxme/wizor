<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас (2026-07-05): **P2 Crawler/Аудит реализован новой методологией** (первая продуктовая фаза, прогнанная автономным циклом ADR-0021): read-only краулер (httpx+Playwright+lxml) + schema-валидатор + crawl_results + Celery + endpoint; verify зелёный (70 тестов, cov 88%), review→fix (закрыты read-only-bypass + SSRF), audit tier-3 PASS-WITH-FIXES (10/10 инвариантов). Ждёт founder-ревью PR + deferred_live_gold (test-WP URL). До этого (2026-07-03): интегрирована методология ORIION → ADR-0020 (исполняемый слой) + ADR-0021 (runner), вмёржена (PR #2/#3), машина ВЫКЛ. P1 Foundation вмёржен. История фаз — PHASE-HISTORY.md. Пишет только memory-curator (шаг 8). -->

# STATUS — WIZOR

**Обновлено:** 2026-07-05 · сессия `oriion-methodology-integration` · @claude-opus
**Стадия:** **P2 Crawler/Аудит реализован** — первая продуктовая фаза, прогнанная новой автономной методологией (ADR-0021) end-to-end: plan→domain→implement→verify→review→audit→memory. Read-only краулер + schema-валидатор + crawl_results + Celery `crawl_site` + endpoint. Verify зелёный (ruff/mypy/70 тестов/cov 88%); review cycle-1 закрыл F1 (Playwright read-only-bypass) + F2/F3 (SSRF) + F5; auditor tier-3 **PASS-WITH-FIXES** (10/10 §6). Ждёт founder-ревью P2 PR. Ранее: методология ORIION вмёржена (ADR-0020/0021, PR #2/#3, машина ВЫКЛ); P1 вмёржен.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту (нужен founder) | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | 🟢 **Реализован, ждёт гейт** (2026-06-24) | `gates/P1-foundation.md` (pending) |
| P2 — Crawler/Аудит | 🟢 **Реализован, ждёт PR-ревью** (2026-07-05) | P2 PR (deferred_live_gold) |
| P3 — AI-Readiness Score | ⏳ Pending | — |
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

**P2 (Crawler/Аудит)** — реализован на ветке `claude/oriion-methodology-integration-o2dp8a` (5 коммитов: seam→persistence→domain→audit→fixes). Прогнан полный 9-шаговый цикл: planner-план (0 эскалаций) → domain-build (crawler-probe-specialist + backend-implementer, параллельно) → verify (70 тестов, cov 88%) → review (CHANGES→fixed) → audit tier-3 (PASS-WITH-FIXES, 10/10 §6). Ключевое: read-only-инвариант §6.1 сделан **структурным** и на browser-пути (Playwright route-abort), закрыт SSRF (private-IP + @context). Ждёт founder-ревью PR (машина ВЫКЛ — авто-мёржа нет). **deferred_live_gold:** живой crawl golden нужен test-WP URL; реальные CWV/индексируемость — founder-ключи (стабы → `deferred`).

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
| 0 | **Ревью P2 PR** (Crawler/Аудит) — reviewer+auditor зелёные, verify 88%; принять/оспорить `deferred_live_gold` (нужен test-WP URL для живого crawl + ключи PageSpeed/Bing/Яндекс для CWV/индексируемости) | P2 PR |
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

Стек залочен (ADR-0011, PRD §12). Продуктовый код: P1 (foundation) + P2 (crawler/аудит, контекст `crawler`, миграция 0002). Харнесс: файл-нативный, 8 ядро + 6 профильных, тиринг по роли, **исполняемая автономия** (ADR-0021, ВЫКЛ).

## Протокол обновления

Только `memory-curator` пишет этот файл (шаг 8 цикла). История завершённых фаз → `PHASE-HISTORY.md`. Этот файл держит ТОЛЬКО rolling-состояние.
