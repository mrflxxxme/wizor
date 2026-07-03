# Autonomy build plan — живой трекер (WIZOR)

Реализует [ADR-0021](../../.planning/decisions/ADR-0021-autonomous-multiphase-runner.md) (8 решений D1–D8, порт ORIION ADR-037). Рельсы (Блок A) предшествуют runner'у: согласие founder'а на full-autonomy merge (D1) обусловлено существованием усиленных гейтов (D2/D3).

Легенда: ✅ готово · 🚧 в работе · ⬜ todo · 🧩 установлено (ждёт вооружения founder'ом)

---

## Блок A — Предохранители (D2/D3) 🧩

- ✅ `tripwire.yaml` — 8 категорий (5 базовых ORIION + WIZOR: autofix_writes / probe_geo / pdn_compliance).
- ✅ `evidence-schema.json` + `verify_evidence.py` — коммит-привязанный evidence (усиливает ADR-0018).
- ✅ `classify_tripwire.py` — diff-классификатор + greenfield-CREATE content-nuance.
- ✅ ADR-0021 + порт-нотация ORIION ADR-037.
- ⬜ `.github/workflows/evidence.yml` — CI-job, гоняет `verify_evidence.py` (устанавливается в этом PR).
- ⬜ **branch protection на `main`** (founder one-time): require PR + checks (`evidence`, `security`), linear history, delete_branch_on_merge.

## Блок B — Фронт-автономия (D4/D5) 🧩

- ✅ `escalation-policy.md` — агент владеет impl+arch (decide+log); эскалирует ТОЛЬКО продукт/рынок (ADR-0017 §5) + tripwire.
- ✅ `judge-panel.md` — широкий форк + N-подходов + рубрика `auditor` (не `evaluator` — лёгкий ростер WIZOR).
- ✅ `log_decision.py` (→ `.planning/_session-context/DECISIONS-LOG.md`).
- ✅ `/autonomy:discuss` — авто-discuss фазы.

## Блок C — Runner (D6/D8) 🧩

- ✅ `/autonomy:run` — цепь `scope→discuss→plan→domain→implement→review→verify→audit→memory→PR→auto-merge|tripwire-pause→next` (9-шаговый цикл charter §4), луп до escalation/ack/stuck/пустой очереди.
- ✅ auto-merge-on-green — явный шаг: `gh pr checks` all-green + `classify_tripwire.py` exit 0 → squash-merge; exit 10 → RUN-QUEUE `ack-needed` + notify.
- ✅ RUN-QUEUE — `run_queue.py` (add/resolve/check-ack/pending) + `/autonomy:ack` (1-клик).
- ✅ notify — PushNotification на 5 interrupt-событиях + опц. Telegram (`notify.json`).
- ✅ premerge tripwire-хук — `premerge_hook.py`. **FOUNDER ACTION:** смёржь `settings.hook-snippet.json` в `.claude/settings.json`.
- ✅ role-loader — `load_role.py` компонует spawn-промпт из `.claude/agents/<role>/` (14 ролей WIZOR); runner передаёт в general-purpose `Task` (ADR-0020 — закрывает разрыв handbook-ролей без конвертации).

## Блок D — Self-healing (D7) 🧩

- ✅ regression-watch — `check_main_health.py`: последний прогон per gate-workflow (`backend`/`frontend`/`security`/`evidence`) на main → вердикт + `offender_sha`.
- ✅ auto-revert + notify — `/autonomy:heal` §2: revert-ветка с свежего main → gated revert-PR → merge → обязательный RUN-QUEUE `revert` + push + Telegram.
- ✅ автономный fix-loop — `/autonomy:heal` §3: cherry-pick → диагноз из `--log-failed` → фикс + закрытие дыры гейта → полные гейты → merge/ack; макс 3 цикла → `stuck`.

## Блок E — Параллелизм (D6) 🧩

- ✅ opt-in worktree-параллелизм — `run.md` §Parallel: только доказуемо-независимые фазы (нет общих `src/wizor/<context>` / нет ребра `depends_on` / не tripwire-heavy); executor-сабагенты `isolation: "worktree"` + background, макс 2 трека; **мёржи всегда сериализованы** через health-check.
- ✅ per-run budget — `run.md` §Budget: оценка в `complete`-запись; панели + fix-loops в dev_team-caps (charter §3.4).

---

## Разрывы / follow-up (до вооружения)

- ⬜ **classify_tripwire.py runtime** — использует PyYAML через backend-venv/`uv run`. Перед арм premerge-хука: PyYAML в backend-окружении, либо stdlib-YAML-шим. Тест: `python scripts/autonomy/premerge_hook.py` на тест-PR.
- ⬜ **evidence.yml** CI-job — установить (этот PR) + сделать required check в branch protection.
- ⬜ **Пилот** — первая автономная фаза (кандидат P2 Crawler): `/autonomy:run P2` после вооружения + Docker + funded `.env`. Ретро: что runner эскалировал/паузил/хилил → подтянуть tripwire-глобы / escalation-policy.
- ⬜ **cost-budget dev_team caps** — сверить per-run cap с charter §3.4 (сейчас per-task $0.40/$1.50, per-day $20/$50, kill $300/мес).
