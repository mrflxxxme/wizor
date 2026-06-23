<!-- HEAD-SUMMARY (≤500т): Append-only лог сессий WIZOR. Одна запись на сессию. Ротация при >300 строк → _session-context/archive/JOURNAL-YYYY-Qn.md. Пишет memory-curator на шаге 8. -->

# JOURNAL — WIZOR (append-only)

## 2026-06-23 · scaffold-bootstrap · @claude-opus (Scaffold v1.0)

- **Scope:** на основе PRD v0.2 собрать поэтапное ТЗ + файл-нативный харнесс ИИ-команды (по образцу ORIION, но токен-эффективнее), упаковать структурой планирования в репо `mrflxxxme/wizor`.
- **Workflow:** интервью (grill-me, 11 развилок через AskUserQuestion) → фиксация 17 решений → keystone `BUILD-CHARTER.md` → фан-аут 7 профильных суб-агентов (Sonnet) параллельно → сборка состоянческих доков → пост-аудит → пуш.
- **17 решений (→ ADR-0001…0016):** файл-нативный субстрат; ядро 8 + 6 профильных по требованию; тиринг по роли + эскалация (Tier-0/Haiku/Sonnet/Opus); 9-шаговый цикл с обязательными пост-аудитом и обновлением памяти; специалисты пишут код своего домена сами (mode B); пост-аудит по риск-тиру (1/3/5 линз) + 10 стоячих инвариантов; курируемый MEMORY-INDEX + summary-first + ротация; роадмап P0–P10 read-only-first; контракт-стабы + JIT; лёгкий PR-на-фазу + тированные CI; RU-нарратив/EN-идентификаторы; авто-README; свой CLAUDE.md; стек залочен (PRD §12); three-track модель доступа (Tier 0/Manual/Auto).
- **Адаптация под PRD v0.2:** добавлена доктрина read-only-first → роадмап пересобран (ценность через Tier 0 + Manual track раньше, auto-fix → P10 апгрейд, gated_by P0); добавлены контексты `patches`/`connectors`, инварианты read-only-границы и honest-forecast.
- **Построено:** 169 файлов (~522 KB). 8 ядро-агентов + 6 профильных + `_shared` + `AGENTS.md`; 11 phase-spec'ов + ROADMAP; 16 ADR + template + index; 13 контракт-стабов + карта; гейты P0/A→B + JSON-schema; `_meta` (charter/conventions/stack/glossary/README); agent-handbook 00–07; OPEN-QUESTIONS/PLACEHOLDERS; STATUS/HANDOFF/MEMORY-INDEX/PROJECT/README/CLAUDE.md.
- **Token-эффективность vs ORIION:** агенты ~10–12 KB (против ~40–50 KB); system-prompt'ы ≤4 KB (ссылка на charter §6, не дублирование); JOURNAL/STATUS/HANDOFF с ротацией и head-summary с дня 1; recall через индекс.
- **Next:** founder запускает P0 (Discovery) и/или заполняет PLACEHOLDERS.
- **Refs:** ветка `main` (initial scaffold); PRD v0.2; `_meta/BUILD-CHARTER.md`.
