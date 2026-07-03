---
description: Self-healing — детект красного main, авто-реверт offending-мёржа, автономный fix-loop (ADR-0021 D7)
argument-hint: "[check | revert <sha> | fix <sha>] (default: check → полный протокол)"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent, TaskCreate, TaskUpdate, ToolSearch
---

# /autonomy:heal — авто-реверт + автономный fix-loop (ADR-0021 D7)

Main должен быть **зелёным по построению**: post-merge регрессия сначала ревертится, потом чинится. Разработка продолжается; fix-loop автономен; о реверте founder УВЕДОМЛЯЕТСЯ ВСЕГДА. Режим: **$ARGUMENTS** (default = полный протокол). Remote: `mrflxxxme/wizor`.

## 1. Детект
`python scripts/autonomy/check_main_health.py` → exit 0 = здоров (готово, отчитайся); exit 20 = JSON-вердикт со списком упавших workflow (`backend`/`frontend`/`security`/`evidence`) + `offender_sha` (squash-merge-коммит, чей head тестировал упавший run); exit 1 = не судить → RUN-QUEUE `stuck` + notify, СТОП (не мёржить ничего вслепую).

Перед ревертом sanity-check атрибуции: `git log origin/main --oneline -5` — подтверди, что `offender_sha` — недавний (runner-era) merge-коммит; если фейл предшествует новейшим мёржам или sha нет на main — СТОП → RUN-QUEUE `stuck` с JSON-вердиктом + notify (мис-атрибуция хуже паузы).

## 2. Реверт (main зелёный по построению)
1. `git fetch origin main` → ветка `fix/revert-<sha7>` с `origin/main`.
2. `git revert --no-edit <offender_sha>` (squash-мёржи — обычные коммиты, прямой реверт; никогда `--force` на main; реверт сам обратим).
3. Конфликт реверта (позже построили сверху) → НЕ решай креативно — RUN-QUEUE `stuck` (details: конфликтующие пути) + notify, СТОП.
4. PR (`revert: <исходный title>` + ссылка на упавший run) → `gh pr checks --watch` → merge. Revert-PR тоже гейтнут (`evidence`/`security` required) — это намеренно.
5. **Notify (обязательно, D7):** RUN-QUEUE `revert` (offender sha/PR, упавшие workflow, fix-ветка) + PushNotification + Telegram (`notify.json`). Founder обязан узнать о каждом реверте, когда он случился.

## 3. Fix-loop (автономный)
1. Ветка `fix/heal-<sha7>` с свежего `origin/main`; `git cherry-pick <offender_sha>` — переприменить реверченную работу (механические конфликты с revert-коммитом резолвь; семантические → `stuck` + notify).
2. Диагностируй из логов упавшего run'а (`gh run view <run_id> --log-failed`; среда без gh → `mcp__github__get_job_logs`) — почини реальную регрессию, добавь/поправь тест, который ДОЛЖЕН был её поймать (регрессия, пережившая гейты = дыра в гейте; закрой её).
3. Полные local-гейты (`make lint test` + evidence-гейты фазы пере-прогнать на новом HEAD) → PR → чеки зелёные → tripwire classify (`classify_tripwire.py`) → merge на exit 0, или RUN-QUEUE `ack-needed` на exit 10 (исходный offender вполне мог быть tripwire-класса — норм, ack).
4. Макс **3 fix-цикла** (charter §4 шаг 5 mirror): всё ещё красно после 3 → RUN-QUEUE `stuck` с полной диагностикой + notify, оставь ветку founder'у.
5. На успехе: закрой историю в RUN-QUEUE (`complete`: revert-PR + fix-PR + root-cause одной строкой) + `log_decision.py --kind impl --fork "regression root-cause" ...`, чтобы audit-trail замкнулся.

## Guardrails
- ОДИН offender за раз: если несколько workflow падают на разных sha, реверти НОВЕЙШИЙ первым, ре-чек health, итерируй.
- Никогда не реверти founder-authored (не-runner) коммит без явного запроса — `stuck` + notify вместо этого.
- Никогда не force-push, не байпась хуки, не резолвь revert-конфликты, выбрасывая работу других фаз.
