# HANDOFF — снапшот сессии

**Обновлено:** 2026-06-23 · `regulation-update-adr0018` · @claude-opus

## Состояние
Scaffold v1.0 собран. Репозиторий содержит полный харнесс ИИ-команды + поэтапное ТЗ (P0–P10) по PRD v0.2. Кода продукта нет.

## Что сделано
- Харнесс: 8 ядро-агентов + 6 профильных + `_shared` (cost-budget, handoff, pipelines) + `AGENTS.md`.
- ТЗ: 11 phase-spec'ов (P0–P10), `ROADMAP.md`, 16 ADR, 13 контракт-стабов + карта, гейты (P0, A→B), `_meta` (charter/conventions/stack/glossary), agent-handbook (00–07), open-items.
- Состояние/память: STATUS, JOURNAL, MEMORY-INDEX, PROJECT, README, CLAUDE.md.
- **Регламент ADR-0017** (gate-only автономия): человек-ревью только на гейтах фаз; внутри фазы агенты автономны (мердж/аудит/доп-сессии сами). Пропагировано по charter/CLAUDE/conventions/handbook/3 pipeline-шаблона (~15 файлов); консистентность проверена grep-свипом (0 активных противоречий).
- **Регламент ADR-0018** (тесты+live-gold перед PR): `verifier` обязан перед PR прогнать unit+integration + live-gold (где возможно), evidence в гейт; невозможно → явный `deferred_live_gold` (не тихо). Пропагировано: charter §12 + шаг 6/9, verifier (3 файла), CLAUDE, conventions DoD, handbook 00/05/07, 3 pipeline-шаблона.

## Следующее действие
**Founder:** запустить Phase 0 (`roadmap/P00-discovery.md`) и/или заполнить `PLACEHOLDERS.md`. Затем — обычный 9-шаговый цикл (см. `_meta/BUILD-CHARTER.md` §4).

## Read-first для следующего агента
1. `_meta/BUILD-CHARTER.md` (charter — целиком)
2. `STATUS.md`
3. `roadmap/P00-discovery.md` (если стартуем P0)
4. `MEMORY-INDEX.md` (для точечного recall)

## Escalate
Нет. Все решения харнесса зафиксированы в ADR-0001…0016.
