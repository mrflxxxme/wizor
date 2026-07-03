---
description: Автономный многофазный runner WIZOR — discuss→plan→execute→gates→PR→auto-merge, сцеплено до escalation/ack/stuck/пустой очереди (ADR-0021 D6/D7)
argument-hint: "[PNN... | next N | until PNN] (default: следующая фаза по STATUS.md)"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent, Skill, TaskCreate, TaskUpdate, ToolSearch
---

# /autonomy:run — автономный многофазный runner (ADR-0021 D6/D7/D8)

Ты — runner. Строгий гейт-стек — merge-authority, НЕ глаза founder'а. Ты сцепляешь фазы В ЭТОЙ сессии (без per-phase ре-bootstrap) до interrupt'а или пустой очереди. Очередь: **$ARGUMENTS** (дефолт — следующая фаза по `.planning/STATUS.md`, таблица «Прогресс роадмапа»).

Каждая фаза проходит **9-шаговый цикл charter §4** (Scope→Plan→Domain→Implement→Review→Verify→Audit→Memory→PR). Runner = автоматизация оркестрации этого цикла + auto-merge на строгих гейтах.

## Контракты (грузи JIT, в этом порядке)
1. `.planning/_meta/BUILD-CHARTER.md` (charter — 1×/сессия) + `.planning/agent-handbook/00-START-HERE.md`.
2. `.claude/autonomy/escalation-policy.md` (D4) + `judge-panel.md` (D5) + `tripwire.yaml` (D2).
3. `.claude/agents/_shared/cost-budget.yaml` — per-task soft $0.40/hard $1.50; per-day soft $20/hard $50; kill $300/мес (charter §3.4).

## Preflight (один раз за run)
- `git rev-parse --show-toplevel` — якорь; синхронизируй `origin/main`; работай с свежего `main`.
- Docker: `docker info`. **НИКОГДА не поднимай Docker сам** (founder-controlled). Down → integration/live-gold недоступны: фазы, чей `evidence/manifest.json` их требует, идут в RUN-QUEUE как `stuck`; берёшь следующую фазу без них.
- Funded `.env`: `python scripts/autonomy/provision_env.py` — копирует канонический funded `backend/.env` (git-ignored на main-checkout) в активный worktree, если отсутствует (идемпотентно; secret-safe: откажет, если dest не в .gitignore; значения не печатает). Exit 0 = есть/провижен; exit 2 = не сконфигурирован → live-gold недоступен, тот же stuck-путь, что Docker-down. НИКОГДА не коммить `.env` (tripwire `secrets_keys_crypto` + gitleaks).
- Бюджет: per-day soft $20 / hard $50 (charter §3.4). Трекай примерный расход; СТОП на hard cap (RUN-QUEUE `stuck`: budget).

## Per-phase цикл
Для каждой фазы P в очереди:

1. **Scope+Branch** — ветка `phase/<PNN>-<slug>` с свежего `origin/main`. Прочитай `roadmap/<PNN>-*.md` (HEAD-SUMMARY первым) + затронутые `contracts/<ctx>/`.
2. **Discuss (D4)** — прогони `/autonomy:discuss <PNN>`: owned-форки решаешь+логируешь (`log_decision.py`); широкие → judge-panel (`auditor`-судья); продукт/трипвайр → эскалация. Эскалация блокирует всю фазу → пропусти P (оставь ветку), продолжи со следующей НЕЗАВИСИМОЙ фазой; иначе иди по разблокированной части.
3. **Plan** — `PLAN.md` ролью `planner` (load_role.py --role planner); задачи через TaskCreate; `wide_fork:`/`escalated:` флаги.
4. **Domain+Implement** — если фаза касается домена, профильный специалист сам пишет код (charter §4 шаг 3; спавн через `load_role.py --role <specialist>`), иначе `*-implementer`. Атомарные коммиты (Conventional Commits, футер `Refs: <PNN>, ADR-NNNN`). Stagnation kill-switch: 30 мин без коммита/файла/статуса → abort, RUN-QUEUE `stuck` + notify (charter §3.4).
5. **Review (≤2 цикла)** — `reviewer` (security-линза при auth/ПДн/audit-log/secrets); >2 циклов → `architect` арбитраж (charter §4 шаг 5).
6. **Verify** — `verifier`: acceptance + `make lint test` (+ integration если Docker up) + пороги гейта. Local-only гейты (live-gold crawl/probe / docker-integration / adversarial audit / judge-panel) ОБЯЗАНЫ писать `evidence/<gate>.json` (схема `.claude/autonomy/evidence-schema.json`, `head_sha` = финальный коммит) + заявить в `evidence/manifest.json`. **Пере-прогони evidence-гейты, если коммитишь после генерации** (freshness форсит CI-job `evidence`, ADR-0018).
7. **Audit (ОБЯЗАТЕЛЬНО)** — `auditor`, риск-тир по фазе (Tier1-2→1, Tier3→3, Tier4→5 линз) + все 10 стоячих инвариантов §6. Вердикт PASS/PASS-WITH-FIXES/BLOCKED; фиксы в цикле; отчёт `_session-context/AUDIT-YYYY-MM-DD-<PNN>/`.
8. **Memory (ОБЯЗАТЕЛЬНО)** — `memory-curator` (единственный писатель): STATUS/HANDOFF(≤2KB)/JOURNAL(+ротация)/MEMORY-INDEX + gate-fill + README-статус + архив аудита (charter §4 шаг 8).
9. **PR** — `gh pr create` (открытым, НЕ draft — ADR-0019; body: what/AC/verify-evidence/decisions-log refs). Watch `gh pr checks <N> --watch`; ВСЕ чеки зелёные обязательны — `backend`/`frontend` (когда триггернулись path-фильтром), `security`, `evidence`. Красный → фикс+re-push, макс 3 цикла → RUN-QUEUE `stuck` + notify, дальше.
10. **Tripwire classify (явный шаг)** — `python scripts/autonomy/classify_tripwire.py --diff-base origin/main` (exit 0 = чисто; 10 = совпало). Premerge-хук ре-чекает это на команде мёржа — defense-in-depth.
    - **exit 0** → `gh pr merge <N> --squash --delete-branch` (linear history).
    - **exit 10** → RUN-QUEUE `ack-needed` (`run_queue.py add --kind ack-needed --pr <N> --phase <PNN> --summary ... --details "Categories: ..."`) + notify. НЕ мёржить. Продолжай следующей фазой ТОЛЬКО если она независима от P; иначе останови цикл (оставь всё зелёным + задокументированным).
11. **Post-merge regression watch (D7)** — не блокируйся на CI main'а каждый мёрж (~3 мин): `python scripts/autonomy/check_main_health.py` (a) ПЕРЕД каждым следующим мёржем и (b) в конце run'а. Exit 20 → протокол `/autonomy:heal` (авто-реверт → notify → fix-loop, макс 3 цикла); возобнови очередь после мёржа фикса, стоп если heal ушёл в `stuck`. Exit 1 (не судить) → без дальнейших мёржей, `stuck` + notify.
12. **Phase complete** — RUN-QUEUE `complete` (одна строка: PR, cost, decisions count). Если фаза закрывает гейт (`gates/*.md`) — заполни hard_thresholds + evidence_url, но `founder_signature` НЕ ставь: подпись гейта = единственный human-checkpoint (ADR-0017). Следующая фаза.

## Interrupts → notify (D8), каждый раз
На 5 событиях — **ack-needed / escalation / revert / stuck / run-complete**:
1. `run_queue.py add ...` (очередь = единственное окно founder'а).
2. `ToolSearch "select:PushNotification"` → PushNotification (короткий title + что ждёт).
3. Если `.claude/autonomy/notify.json` есть и в нём `telegram_chat_id` → тот же месседж в Telegram (phone-ack). Нет/фейл → desktop push + очередь достаточно; никогда не блокируйся на фейле нотификации.

`/autonomy:ack <ID> approved` (founder, из любой сессии) разблокирует мёрж — premerge-хук чтит `run_queue.py check-ack`.

## Parallel tracks (Block E — opt-in, D6)
Секвенциально — ДЕФОЛТ. Параллель ТОЛЬКО когда фазы **доказуемо независимы**: нет общих bounded-context'ов (сверь `src/wizor/<context>` + migration-dirs фаз), нет ребра зависимости в `ROADMAP.md`/`depends_on`, ни одна не tripwire-heavy. Тогда:
- Спавн per-phase executor-сабагентов через Agent tool с `isolation: "worktree"` + `run_in_background: true` (макс **2** трека), каждый — своя ветка + PR через полный per-phase цикл (шаги 2–8).
- **Мёржи СЕКВЕНЦИАЛЬНЫ** через шаги 10–11 в главной сессии (один мёрж → health-check → следующий). Никогда два трека подряд без health-check между — атрибуция регрессии (D7) требует одного offender'а за раз.
- Любое сомнение в независимости — не параллель. Сэкономленное wall-clock не стоит кросс-трек-конфликта.

## Budget accounting (charter §3.4)
В конце run'а оцени расход (фазы × avg task cost vs cost-budget.yaml) в `complete`-запись RUN-QUEUE. Judge-панели и heal fix-loops считаются в тот же per-day бюджет; деградируй панель N=3→2 при поджиме (judge-panel.md).

## Stop conditions (заверши run чисто)
Очередь пуста · escalation/ack блокирует все оставшиеся фазы · budget hard-cap · heal ушёл в `stuck` (нечинимая регрессия) · founder сказал стоп. На стопе: RUN-QUEUE `complete`-сводка за RUN (смёржено / pending acks / эскалации / реверты+фиксы / оценка расхода) + notify.

## Hard rules
- НИКОГДА не мёржить без: все CI-чеки зелёные + evidence свежий + tripwire exit 0 (или approved ack) + main healthy (check_main_health exit 0) + `auditor` PASS/PASS-WITH-FIXES + `reviewer` APPROVE (charter §4 шаг 9).
- НИКОГДА не байпасить хуки (`--no-verify`), никогда `--force` (только `--force-with-lease` на feature-ветках).
- НИКОГДА не выдумывать `TBD_*` значения (PLACEHOLDERS.md — литералы); не поднимать Docker; не трогать реальный клиентский prod (ADR-0017 §6 — вне dev-автономии).
- Necessary human-checkpoint = только `founder_signature` на гейте фазы. Per-PR аппрув упразднён (ADR-0017).
- Parallel tracks: макс 2, только доказуемая независимость, мёржи всегда сериализованы.
- Среда без `gh` (напр. Claude Code web): используй эквивалентные `mcp__github__*` MCP-инструменты (create_pull_request / pull_request_read / merge_pull_request / get_job_logs).
