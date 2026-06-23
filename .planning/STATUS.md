<!-- HEAD-SUMMARY (≤500т): Rolling-состояние WIZOR. Сейчас: scaffold v1.0 собран (2026-06-23) — харнесс ИИ-команды + полное ТЗ (P0–P10) готовы; кода продукта ещё нет. Следующий шаг: founder запускает Phase 0 (Discovery) ИЛИ заполняет критичные PLACEHOLDERS. История фаз — в PHASE-HISTORY.md. Обновляет этот файл только memory-curator на шаге 8 цикла. -->

# STATUS — WIZOR

**Обновлено:** 2026-06-23 · сессия `regulation-update-adr0017` · @claude-opus
**Стадия:** Scaffold v1.0 + регламент ADR-0017 (gate-only автономия) → готов к Phase 0.

## Прогресс роадмапа

| Фаза | Статус | Гейт |
|---|---|---|
| **Scaffold** (харнесс + ТЗ) | ✅ **Завершён** (2026-06-23) | — |
| P0 — Discovery & De-risking | ⏳ Готов к старту | `gates/P0-to-heavy-autofix.md` |
| P1 — Foundation | ⏳ Pending | — |
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

Нет активной фазы. Харнесс собран; ожидается решение founder о старте **P0 (Discovery)** — он может идти параллельно с P1–P5 (инфра), тяжёлый auto-fix (P10) гейтится прохождением P0.

## Блокеры / действия founder

| # | Действие | Где |
|---|---|---|
| 1 | Запустить P0 (Discovery) — 30 CustDev-интервью + тех-спайки | `roadmap/P00-discovery.md` |
| 2 | Заполнить критичные TBD-токены (Yandex Cloud, ЮKassa, LLM-ключи, юрлицо) | `PLACEHOLDERS.md` |
| 3 | Снять открытые вопросы продукта | `OPEN-QUESTIONS.md` |

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
