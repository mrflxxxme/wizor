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

## 2026-06-23 · regulation-update-adr0017 · @claude-opus (ADR-0017)

- **Scope:** запрос founder — на ревью приходят только гейты фаз; всё внутри фазы агенты выполняют сами, включая запуск доп. сессий Claude Code и управление контекстным окном.
- **Решение:** ADR-0017 (phase-gate-only autonomy), **amends ADR-0009**. Человек-чекпоинт = только exit-гейт фазы (`founder_signature`); внутри фазы PR авто-мерджятся (CI + `reviewer` + `auditor` PASS); агенты спавнят доп-сессии (Agent tool / headless `claude -p`) для параллелизма и контекст-менеджмента. Guardrails: глубина спавна ≤2, ≤8 сессий, cost/stagnation kill-switch, каждый юнит пишет handoff. Граница: необратимые внешние действия (реальный prod / деньги / DPA / внешние коммуникации) — под trust-ladder/DPA (ADR-0015), не dev-автономия.
- **Пропагация (~15 файлов):** charter (§2 #18, §4 шаг 9, новый §11, v1.1); CLAUDE.md (Git/PR + новая секция «Автономия»); conventions (tier-review → audit-depth); agent-handbook 00/02/03/05/07; decisions/README + ADR-0009 (amended-banner + `amended_by` frontmatter); 3 pipeline-шаблона (`pr-approve` → `pr-auto-merge` + `phase-gate`); memory-curator handoff; README (how-to-use + 9-шаговая строка).
- **Верификация:** grep-свип — 0 активных противоречий (остались только размеченные исторические упоминания в теле ADR-0009).
- **Урок процесса:** build-суб-агент оборвался на середине и работал аддитивно (добавлял, не убирал старое) — пропагацию доделал и сверил вручную grep-свипом. Вывод: после делегированной правки регламента ОБЯЗАТЕЛЕН verify-свип на остаточные противоречия.
- **Next:** founder запускает P0 — теперь автономно до гейта.
- **Refs:** ADR-0017; amends ADR-0009; charter v1.1.

## 2026-06-23 · regulation-update-adr0018 · @claude-opus (ADR-0018)

- **Scope:** запрос founder — агенты обязаны сами прогонять тесты + live-gold перед PR (где возможно); автономность внутри фаз должна быть ПОДТВЕРЖДЕНА результатами проверок.
- **Решение:** ADR-0018 (mandatory self-run tests + live-gold before PR), **amends ADR-0017**. `verifier` (шаг 6) перед PR обязан: unit+integration зелёные + coverage-гейт; live-gold (end-to-end против реальных сервисов с golden-набором) где возможно. Evidence → `_session-context/VERIFY-<phase>-<ts>.md` (секции `## Tests` / `## Live-gold`), гейт ссылается через `evidence_url`. **No-silent-skip:** live-gold невозможен → явный `deferred_live_gold` (reason/what/founder_action), founder видит на гейте. Авто-мердж = CI + reviewer + auditor + verify(тесты+live-gold/deferral). Live-gold по треку: read-only→crawl/probe golden; infra→smoke PG/Redis/Keycloak; auto(P10)→founder-owned тест-WP + rollback.
- **Пропагация:** ADR-0018; verifier (system-prompt/workflows/gate-check); charter (§2 #19, шаг 6, шаг 9, новый §12, v1.2); CLAUDE.md; conventions (DoD); decisions/README; handbook 00/05/07; 3 pipeline-шаблона (verify checks).
- **Next:** founder заполняет funded-ключи в `PLACEHOLDERS.md` (нужны для live-gold LLM/probe-фаз); запуск P0.
- **Refs:** ADR-0018; amends ADR-0017; charter v1.2.
