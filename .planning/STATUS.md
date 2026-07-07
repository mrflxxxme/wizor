<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас (2026-07-05): **P5 Probe-мониторинг реализован новой методологией** — dual-geo probe 4 моделей (§6.4 структурно: ноль РФ-IP к ChatGPT/Perplexity), N≥5+CI (переиспользует P4 uncertainty), Visibility-метрики; review CHANGES→fixed (метрики были инертны — brand_terms не прокидывались; honest SoV-label) + audit tier-3 **PASS-WITH-FIXES** (§6.4 атакован 6 путей, 0 утечек); verify зелёный (182 теста, cov 88.2%). Ждёт founder-ревью P5 PR. Вмёржено ранее: P4 LLM-router (#6), P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1. Машина ВЫКЛ. Пишет только memory-curator (шаг 8). -->

# STATUS — WIZOR

**Обновлено:** 2026-07-05 · сессия `oriion-methodology-integration` · @claude-opus
**Стадия:** **P5 Probe-мониторинг реализован** (tier-3, read-only) — dual-geo probe 4 LLM-моделей (Алиса/GigaChat RU-ноды; ChatGPT/Perplexity зарубежные ноды+прокси), N≥5+CI (переиспользует P4 uncertainty), Visibility-метрики (Coverage/SoV/Citation/Stability) + Celery batch + `GET /visibility` + версионируемые промпты. Verify зелёный (182 теста, cov 88.2%); review **CHANGES→fixed** (метрики были инертны в prod — brand_terms не прокидывались через шов; honest SoV `has_competitor_data`-label); auditor tier-3 **PASS-WITH-FIXES**. Ключевое: **§6.4 dual-geo структурно** (egress выводится из модели; foreign-модель без прокси → refused, 0 dispatch; атакован 6 путей → 0 утечек). Ждёт founder-ревью P5 PR. Вмёржено: P4 LLM-router (#6), P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту (нужен founder) | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | 🟢 **Реализован, ждёт гейт** (2026-06-24) | `gates/P1-foundation.md` (pending) |
| P2 — Crawler/Аудит | ✅ **Вмёржен** (PR #4, 2026-07-05) | deferred_live_gold (test-WP) |
| P3 — AI-Readiness Score | ✅ **Вмёржен** (PR #5, 2026-07-05) | — |
| P4 — LLM-router | ✅ **Вмёржен** (PR #6, 2026-07-05) | deferred_live_gold (funded keys) |
| P5 — Probe-мониторинг | 🟢 **Реализован, ждёт PR-ревью** (2026-07-05) | P5 PR (deferred_live_gold) |
| P6 — Рекомендации/gap/патчи/forecast | ⏳ Pending | — |
| P7 — Tier 0 Instant Audit (no-auth) | ⏳ Pending | — |
| P8 — Верификация (Manual proof-loop) | ⏳ Pending | — |
| P9 — Auth/биллинг/дорожки | ⏳ Pending | — |
| P10 — Auto track (auto-fix) | ⏳ Pending (gated_by P0) | — |
| → A→B gate | ⏳ Pending | `gates/A-to-B.md` |
| Phase B / C | 🧭 Рамочно (PRD §10–11) | — |

## Текущая активная фаза

**P5 (Probe-мониторинг)** — реализован на ветке `claude/oriion-methodology-integration-o2dp8a` (2 seam→domain+persistence параллельно→reconcile→fix). Цикл: план (0 эскалаций) → domain-build `crawler-probe-specialist` (dual-geo runner) ‖ `backend-implementer` (probe_runs/prompt_sets/visibility_metrics миграция 0005 + Celery batch + метрики + `GET /visibility`) → verify (182 теста, cov 88.2%) → review **CHANGES-REQUESTED** → fix cycle-1 → audit tier-3 **PASS-WITH-FIXES**. Ключевое: **§6.4 dual-geo структурно** (egress выводится из модели, не инъектируем; foreign-модель без прокси → `ProbeGeoViolationError`, 0 dispatch, никогда не RU; атакован 6 путей → 0 утечек); N≥5+CI (переиспользует P4 t-interval); honest-forecast (SoV=coverage-прокси, помечен `has_competitor_data=False`). Review нашёл реальный баг: метрики были инертны в prod (brand_terms не прокидывались → Visibility≡15.0/сайт) → исправлено (per-site brand_terms из URL сайта через шов). Ждёт founder-ревью P5 PR (машина ВЫКЛ). **deferred_live_gold:** живые probe нужны funded-ключи + зарубежная egress-нода. **Deferred→P6/P8/P9:** rich entity brand-terms (P6), competitor SoV (P6), probe_runs↔prompt_set_version (P8), site RLS (P9).

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
| 0 | **Ревью P5 PR** (Probe-мониторинг) — review CHANGES→fixed + audit tier-3 PASS-WITH-FIXES, verify 88.2%; §6.4 dual-geo верифицирован под атакой (6 путей) | P5 PR |
| 0а | Дать **funded LLM-ключи + зарубежную probe-egress-ноду** (Hetzner/Selectel + резидентный прокси) — снимет P5/P4 `deferred_live_gold`; **test-WP URL** + PageSpeed/Bing/Яндекс — снимет P2, включит CWV/индексируемость в Score | `PLACEHOLDERS.md` |
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
