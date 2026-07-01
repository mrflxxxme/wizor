<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас: P1 Foundation реализован (2026-06-24) — monorepo (FastAPI+PG/pgvector+Redis+Celery+Keycloak/PostHog skeleton, multi-tenant, 3 CI workflow); первый продуктовый код. Review APPROVE / Audit PASS-WITH-FIXES (10/10 инвариантов) / verify зелёный локально + live-gold в CI. Ждёт: зелёный CI финального коммита + founder_signature на gates/P1-foundation.md. История фаз — в PHASE-HISTORY.md. Обновляет этот файл только memory-curator на шаге 8 цикла. -->

# STATUS — WIZOR

**Обновлено:** 2026-06-24 · сессия `P1-foundation` · @claude-opus
**Стадия:** P1 Foundation реализован (monorepo + CI); первый продуктовый код. Ждёт зелёный CI + `founder_signature` на гейте P1.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту (нужен founder) | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | 🟢 **Реализован, ждёт гейт** (2026-06-24) | `gates/P1-foundation.md` (pending) |
| P2 — Crawler/Аудит | ⏳ Pending | — |
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

**P1 (Foundation)** — код реализован на ветке `claude/quirky-allen-meae1a`, draft PR открыт. Прошёл review (APPROVE-WITH-COMMENTS) + audit (PASS-WITH-FIXES, 10/10 инвариантов) + verify (локально зелёный; live-gold стека — в CI). Фаза закрывается founder-подписью гейта после подтверждения зелёного CI.

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
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

Стек залочен (ADR-0011, PRD §12). Кода продукта нет. Харнесс: файл-нативный, 8 ядро-агентов + 6 профильных, тиринг по роли.

## Протокол обновления

Только `memory-curator` пишет этот файл (шаг 8 цикла). История завершённых фаз → `PHASE-HISTORY.md`. Этот файл держит ТОЛЬКО rolling-состояние.
