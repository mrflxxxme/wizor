# `.claude/autonomy/` — конфиг автономного runner'а + предохранители

Source-of-truth автономного многофазного runner'а WIZOR ([ADR-0021](../../.planning/decisions/ADR-0021-autonomous-multiphase-runner.md), порт ORIION ADR-037). Под runner'ом **усиленный гейт-стек — merge-authority, а не глаза founder'а** — поэтому эти рельсы должны существовать и быть зелёными *до* включения автономии. Операционализирует ADR-0017 (gate-only автономия) + ADR-0018 (evidence) исполняемой машиной.

## Блоки (ADR-0021 D1–D8)

Живой трекер: [`BUILD-PLAN.md`](./BUILD-PLAN.md).

| Блок | Что | Статус |
|---|---|---|
| **A — Рельсы** | evidence-схема + `evidence` CI-job + tripwire-конфиг + branch protection | 🧩 установлен, ждёт вооружения founder'ом |
| **B — Фронт** | escalation-policy + judge-panel + decisions-log | 🧩 установлен |
| **C — Runner** | `/autonomy:run` + auto-merge-on-green + RUN-QUEUE + `/autonomy:ack` + premerge-хук + role-loader + notify | 🧩 установлен, ждёт вооружения |
| **D — Self-healing** | `check_main_health.py` + `/autonomy:heal` (auto-revert → notify → fix-loop) | 🧩 установлен |
| **E — Параллелизм** | opt-in worktree-треки (макс 2, сериализованные мёржи) + budget-учёт | 🧩 в `run.md` §Parallel |

## Файлы здесь

| Файл | Роль |
|---|---|
| `tripwire.yaml` | **D2 задняя растяжка.** Path-глобы 8 категорий, которые НЕ auto-merge'ятся (миграции · auth/IAM · billing · секреты · публичные контракты · **auto-fix write** · **probe-geo** · **ПДн/152-ФЗ**). Runner классифицирует diff PR'а; совпадение → RUN-QUEUE + notify + ждёт founder `/ack`. |
| `evidence-schema.json` | **D3 целостность гейтов.** JSON-Schema коммит-привязанного evidence-артефакта (усиливает live-gold ADR-0018 до неподделываемого). |
| `escalation-policy.md` | **D4 передняя эскалация.** Что агент владеет (impl+arch, decide+log) vs эскалирует (продукт/рынок + tripwire). Читается `/autonomy:discuss`. |
| `judge-panel.md` | **D5 оптимальность.** Триггер широкого форка + N-подходов + рубрика `auditor` + winner/graft + evidence. |
| `BUILD-PLAN.md` | Живой трекер Блоков A–E (вкл. founder-owned переключатели). |
| `settings.recommended.json` | **Founder-armed.** Permission-allowlist + SessionStart-хук. `cp` в `.claude/settings.json`. |
| `session-start.hook.sh` | **Founder-armed.** Скрипт авто-контекста. `cp` в `.claude/hooks/session-start.sh`. |
| `settings.hook-snippet.json` | **Founder-armed.** Premerge tripwire-хук — смёржь `hooks` в `.claude/settings.json`. |
| `notify.json` | `{"telegram_chat_id": "..."}` — включает Telegram phone-ack (D8). Пусто → desktop push + RUN-QUEUE. |

Скрипты (`scripts/autonomy/`): `verify_evidence.py` (D3) · `classify_tripwire.py` (D2) · `log_decision.py` (D4) · `run_queue.py` (D8) · `premerge_hook.py` (D2 хук) · `load_role.py` (композитор spawn-промпта роли, ADR-0020) · `check_main_health.py` (D7) · `provision_env.py` (preflight funded `.env`).
Команды: `/autonomy:discuss <PNN>` (D4) · `/autonomy:run [queue]` (D6 runner) · `/autonomy:ack [RQ-ID verdict]` (founder resolve) · `/autonomy:heal` (D7).

## Evidence-протокол (D3) — как фаза доказывает local-only гейт

GitHub CI не может прогнать funded live-gold, Docker-интеграцию или адверсариальный аудит. Фаза, которая их гоняет, обязана оставить **коммит-привязанное доказательство** (усиливает ADR-0018):

1. Гейт-скрипт пишет `evidence/<gate>.json` по `evidence-schema.json`, с `head_sha` = точный коммит прогона и `verdict` = `PASS`/`FAIL`.
2. Фаза заявляет требуемые гейты в `evidence/manifest.json`:
   ```json
   { "phase": "P2", "required_gates": ["live_golden_crawl", "adversarial_audit"] }
   ```
3. Workflow `evidence.yml` гоняет `verify_evidence.py` — ассертит: каждый заявленный гейт существует, **свежий** (`head_sha` == PR head), `PASS`. Иначе мёрж заблокирован.

**Свежесть — это зубы:** закоммитил код после генерации evidence → tip ветки ушёл, evidence протух → CI красный → гейт пере-прогнать против финального коммита. Агент физически не может смёржить зелёное, заявив гейт, который не гонял против смёрженного кода. `evidence/` — ещё и post-hoc audit-trail founder'а. `verify_evidence.py` — stdlib-only (bare `python`), exit 0 при отсутствии манифеста (фазы без local-only гейтов не затронуты).

### Прогон верификатора локально
```sh
python scripts/autonomy/verify_evidence.py            # против `git rev-parse HEAD`
python scripts/autonomy/verify_evidence.py --head-sha <sha>
```

## Вооружение — founder one-time actions (машина ставится ВЫКЛЮЧЕННОЙ)

Слой установлен, но **не вооружён** — как в ORIION, автономия включается сознательно founder'ом:

```sh
# 1. Permission-allowlist + SessionStart авто-контекст
cp .claude/autonomy/settings.recommended.json .claude/settings.json
cp .claude/autonomy/session-start.hook.sh      .claude/hooks/session-start.sh

# 2. (опц., после доверия) premerge tripwire-хук — смёржь ключ `hooks` из
#    settings.hook-snippet.json в .claude/settings.json. Требует PyYAML в backend-venv.

# 3. (опц.) branch protection на main: require PR + checks (evidence, security),
#    linear history, delete_branch_on_merge. (gh api / GitHub settings.)

# 4. (опц.) Telegram phone-ack: впиши telegram_chat_id в notify.json.
```

После вооружения: пилот на первой автономной фазе — `/autonomy:run P2` (founder заранее поднимает Docker + funded `.env`). До вооружения слой безопасен: скрипты/команды доступны, но ничто не авто-мёржит и не авто-исполняется.

## Оркестрация сессий — ГДЕ спавнить (урок 2026-07-05)

**Правило:** работу фазы, которая обязана закончиться `git push` + PR, ВЫПОЛНЯЙ в сессии с доступом к репозиторию (эта основная сессия) и делегируй тяжёлое суб-агентам **Agent tool** — они наследуют repo/git-доступ родителя (так собраны P2/P3/P4). НЕ офлоуди такую работу в свежую сессию через `fire_trigger` / `create_new_session_on_fire` (claude-code-remote).

**Почему (инцидент P4):** spawned fresh-сессия (`fire_trigger`) поднимается tool/credential-ограниченной — БЕЗ `mcp__github__*` и БЕЗ repo-write; она «не дотягивается до репозитория», её работа (если есть) остаётся в изолированном workspace и НЕ доходит до `origin`, PR не создаётся. Проверено: после такого спавна `origin` и локальный клон не содержали ни коммитов, ни ветки, ни PR фазы.

**Когда fresh-session-per-fire уместна:** самодостаточные задачи БЕЗ обязательного push/PR (напр. анализ, отчёт, ресёрч) — там ограниченный тулинг не мешает. Для фазовой разработки — только основная сессия + Agent-суб-агенты; при приближении к контекст-бюджету — handoff (HANDOFF.md) и продолжение в новой ИНТЕРАКТИВНОЙ сессии (не через триггер), которая имеет полный тулинг.
