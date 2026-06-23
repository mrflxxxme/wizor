# CLAUDE.md — WIZOR (проектные правила харнесса)

> **Проект.** WIZOR — AI Readiness Platform для РФ. Разрабатывается соло-фаундером + командой профильных ИИ-агентов по **файл-нативному** воркфлоу (по образцу ORIION, но легче и токен-эффективнее).
>
> **Источник истины по воркфлоу:** [`.planning/_meta/BUILD-CHARTER.md`](.planning/_meta/BUILD-CHARTER.md) — читай его целиком один раз за сессию. Продукт: [`.planning/PRD.md`](.planning/PRD.md).
>
> Этот проект **не зависит** от глобального ruflo/claude-flow MCP. claude-flow — опциональный поздний ускоритель памяти, по умолчанию выключен (ADR-0001).

## Первое действие в сессии (context-loading)

1. `.planning/_meta/BUILD-CHARTER.md` (charter — целиком).
2. `.planning/STATUS.md` + `.planning/HANDOFF.md` (где мы).
3. Своя папка `.claude/agents/<role>/` (если ты профильный агент).
4. phase-spec активной фазы (`.planning/roadmap/PNN-*.md`).
5. Затронутые контракты (`.planning/contracts/<ctx>/`).

**Не грузи превентивно.** Остальное — JIT через `.planning/MEMORY-INDEX.md`. У больших доков читай `HEAD-SUMMARY` первым. Приближаешься к 120 KB контекста — делегируй суб-агенту или сделай handoff + новую сессию.

## Цикл фазы (9 шагов) — обязателен

Scope → Plan(pinned) → Domain-build(специалист сам пишет) → Implement → Review(≤2 цикла) → Verify → **⭐Post-audit (риск-тир)** → **⭐Memory-update** → PR+аппрув.

Шаги 7 (пост-аудит) и 8 (обновление памяти) **обязательны всегда** — фаза не закрыта без них.

## Ростер и тиринг

- **Ядро (8):** planner·architect (Opus); backend-implementer·frontend-implementer·reviewer (Sonnet); verifier·memory-curator (Haiku); auditor (Opus).
- **Профильные по требованию (6):** geo-domain-expert·llm-router-specialist·compliance-152fz-specialist (Opus); crawler-probe·cms-connector·devops-infra (Sonnet). Спавнятся ТОЛЬКО когда фаза касается домена.
- **Tier-0** (тривиальные правки) — `Edit` без LLM-агента. Эскалация вверх по флагу `complexity:high`; fallback вниз — только лёгкие роли, **никогда** security/ПДн.
- Оркестратор = founder + главная сессия.

## Память (файл-нативная)

- `memory-curator` — **единственный** писатель состояния/памяти.
- Recall = `MEMORY-INDEX.md` + summary-first (не векторный поиск).
- Ротация: JOURNAL >300 строк → архив; STATUS только rolling; HANDOFF ≤2 KB.
- MUST-NOT в памяти: секреты, полный код, чужой контент (только ссылки).

## Git / PR / CI

- Ветка-на-фазу `phase/PNN-slug`; атомарные коммиты (Conventional Commits, футер `Refs: PNN, ADR-NNNN`).
- AI `reviewer`+`auditor` ревьюят в PR; **founder — единственный человек-апрувер на tier 3+**; tier 1–2 авто-мердж на зелёном CI.
- CI-гейты: lint · type-check · tests · security/secrets · migration-safety. Любой красный = блок мерджа.

## Стоячие инварианты (проверяются в каждом аудите)

read-only-граница (DPA/API — гейт только Auto track) · honest-forecast (нет гарантированных Visibility-%) · auto-fix idempotent+reversible+append-only-log+DPA · ноль РФ-IP к ChatGPT/Perplexity · llms.txt вне citation-score · ПДн в РФ · uncertainty (N≥5+CI) · multi-tenant изоляция · секреты не в коде · FAQ не авто-применяется. Детали — charter §6.

## Поведенческие правила

- Делай ровно то, что просят; не создавай файлы без необходимости; редактируй существующее вместо создания нового.
- Не сохраняй рабочие файлы/тесты в корень — следуй структуре `.planning/` и `.claude/`.
- ВСЕГДА читай файл перед правкой. НИКОГДА не коммить секреты/.env.
- Запускай тесты после изменений; верифицируй сборку перед коммитом.
- Язык: нарратив RU, идентификаторы/код EN.
