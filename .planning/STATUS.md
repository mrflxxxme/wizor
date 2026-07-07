<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас (2026-07-07): **P5 Probe-мониторинг реализован новой методологией** — dual-geo probe 4 моделей (§6.4 структурно: ноль РФ-IP к ChatGPT/Perplexity), N≥5+CI (переиспользует P4 uncertainty), Visibility-метрики. Вмёржено P5 и hotfix Celery-воркера (#8, 7a1ab1e). Ожидает: founder-ревью P5 PR; ключи для live-gold deferred. Ранее: P4 LLM-router (#6), P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1. Машина ВЫКЛ. Пишет только memory-curator (шаг 8). -->

# STATUS — WIZOR

**Обновлено:** 2026-07-07 · grill-интервью (уточнение методологии) · @claude-fable
**Методология уточнена (grill-интервью founder'а, ADR-0022–0028):** live-gold mock/live-классы AC; дефолты P9/P10 (trial 14/30, trust-ladder, Manual=Auto); prompt-set авто-ген; async Tier-0; frontend UI-SPEC (16 экранов) + frontend-AC в P6–P10; новая инфра-фаза **P6.5 Production deploy**; golden e2e = DoD MVP в A→B gate. **Автономная машина ВООРУЖЕНА** (settings.json + session-start + premerge tripwire-хук; branch protection — за founder). Открытые вопросы §6/7/8 → in-progress (дефолты зафиксированы). Charter v1.5.

**Стадия:** **P5 Probe-мониторинг реализован** (tier-3, read-only) — dual-geo probe 4 LLM-моделей (Алиса/GigaChat RU-ноды; ChatGPT/Perplexity зарубежные ноды+прокси), N≥5+CI (переиспользует P4 uncertainty), Visibility-метрики (Coverage/SoV/Citation/Stability) + Celery batch + `GET /visibility` + версионируемые промпты. Verify зелёный (182 теста, cov 88.2%); review **CHANGES→fixed** (метрики были инертны в prod — brand_terms не прокидывались через шов; honest SoV `has_competitor_data`-label); auditor tier-3 **PASS-WITH-FIXES**. Ключевое: **§6.4 dual-geo структурно** (egress выводится из модели; foreign-модель без прокси → refused, 0 dispatch; атакован 6 путей → 0 утечек). Ждёт founder-ревью P5 PR. Вмёржено: P5 (#7, после верификации; hotfix Celery-воркера #8 7a1ab1e закрыл Docker-дефекты), P4 LLM-router (#6), P3 Score (#5), P2 Crawler (#4), методология ORIION (#2/#3), P1.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту (нужен founder) | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | 🟢 **Реализован, ждёт гейт** (2026-06-24) | `gates/P1-foundation.md` (pending) |
| P2 — Crawler/Аудит | ✅ **Вмёржен** (PR #4, 2026-07-05) | deferred_live_gold (test-WP) |
| P3 — AI-Readiness Score | ✅ **Вмёржен** (PR #5, 2026-07-05) | — |
| P4 — LLM-router | ✅ **Вмёржен** (PR #6, 2026-07-05) | deferred_live_gold (funded keys) |
| P5 — Probe-мониторинг | ✅ **Вмёржен** (PR #7 + hotfix #8, 2026-07-07) | deferred_live_gold (funded keys) |
| P6 — Рекомендации/gap/патчи/forecast/PromptSetGen/кабинет | ⏳ Pending (спека уточнена grill-интервью) | — |
| P6.5 — Production deploy (YC IaC) ⭐NEW | ⏳ Pending (ADR-0027; параллельно P6) | `gates/P065-production-deploy.md` |
| P7 — Tier 0 Instant Audit (no-auth, async) | ⏳ Pending | — |
| P8 — Верификация (Manual proof-loop) | ⏳ Pending | — |
| P9 — Auth/биллинг/дорожки | ⏳ Pending | — |
| P10 — Auto track (auto-fix) | ⏳ Pending (gated_by P0) | — |
| → A→B gate | ⏳ Pending | `gates/A-to-B.md` |
| Phase B / C | 🧭 Рамочно (PRD §10–11) | — |

## Текущая активная фаза

**Между P5 и P6 — уточнение методологии (grill-интервью founder'а, 2026-07-07).** P5 (Probe-мониторинг) вмёржен (PR #7 + hotfix #8). Проведено углублённое интервью (11 развязок) → технической документации приданы недостающие для автономного исполнения слои: **ADR-0022–0028** + новая фаза **P6.5 Production deploy** + `UI-SPEC.md` (16 экранов) + frontend-scope/AC в P6–P10 + классы AC (mock/live) + async Tier-0 + prompt-set авто-ген + дефолты P9/P10 + golden e2e (DoD MVP). Charter → v1.5, ROADMAP → v1.1, ADR-индекс → 28. Машина **вооружена**. Открытые вопросы §6/7/8 → in-progress.

**Следующее (после подписи P1 founder'ом):** **P6 (Рекомендации + PromptSetGen + первый авторизованный кабинет)** — зависит P3+P5 (оба вмёржены). Параллельно **P6.5 (Production deploy)** — devops-фаза, требует founder-ресурсов (YC-аккаунт + домен). **Deferred из P5 → адресованы:** competitor SoV / rich entity brand-terms (P6), probe_runs↔prompt_set_version binding (ADR-0024, P6), site RLS (P9).

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
| 0 | ✅ **P5 вмёржен** (PR #7 + hotfix #8, 2026-07-07) — действие снято | — |
| 0а | ✅ **Машина вооружена** (grill 2026-07-07): settings.json + session-start + premerge tripwire-хук. **Остаётся founder:** branch protection на main (require PR + evidence/security checks, linear history) — GitHub-admin действие; опц. `notify.json` Telegram-ack | `.claude/autonomy/README.md` §Вооружение |
| 1 | **Подписать гейт P1** — CI финального коммита 76641f6 зелёный (подтверждён), 8 порогов PASS | `gates/P1-foundation.md` (`founder_signature`) |
| 2 | ⭐ **Дать минимальный live-gold-набор ДО старта P7** (ADR-0022): **test-WP URL** + **funded LLM-ключи** (GigaChat/YandexGPT/OpenAI/Perplexity) + **зарубежная egress-нода** + резидентный прокси + **PostHog-инстанс** + **ЮKassa sandbox** (~3–5 тыс ₽/мес). Снимает live-only AC каскада P6–P10 | `PLACEHOLDERS.md` |
| 3 | Запустить P0 (Discovery) — 30 CustDev-интервью + тех-спайки (требует founder). Ревалидирует дефолты ADR-0023 (open-Q §6/7/8) | `roadmap/P00-discovery.md` |
| 4 | Заполнить критичные TBD-токены (Yandex Cloud + домен для P6.5, ЮKassa, LLM-ключи, юрлицо) | `PLACEHOLDERS.md` |
| 5 | Принять/оспорить deferred: DLG-1 PostHog self-host (→P6.5/P7), DLG-2 `make dev-bootstrap` локально (нужен Docker) | гейт P1, секция deferred_live_gold |

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
