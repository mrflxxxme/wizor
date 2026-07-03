---
description: Разрешить запись RUN-QUEUE — founder 1-клик ack для tripwire-мёржей и эскалаций (ADR-0021 D2/D8)
argument-hint: "[RQ-ID approved|rejected [note]] (без аргументов: список pending)"
allowed-tools: Read, Bash
---

# /autonomy:ack — founder ack/resolve для interrupt-очереди runner'а

Аргументы: **$ARGUMENTS**

## Без аргументов → покажи, что ждёт
`python scripts/autonomy/run_queue.py pending` и покажи founder'у каждую pending-запись **полным блоком** из `.planning/_session-context/RUN-QUEUE.md` (summary, categories, resolve-hint). Для `ack-needed`-записей ещё покажи ссылку на PR + компактный risk-digest: `gh pr view <N> --json title,additions,deletions,files` — перечисли ТОЛЬКО tripwire-совпавшие файлы (1-клик founder'а — про них, не про весь diff). Среда без `gh` → `mcp__github__pull_request_read`.

## `<RQ-ID> approved|rejected [note...]`
1. `python scripts/autonomy/run_queue.py resolve <RQ-ID> --verdict <verdict> --note "<note>"`.
2. Если запись `ack-needed` с `pr:<N>` и вердикт **approved**:
   - Premerge-хук теперь разрешает мёрж (`check-ack` проходит). Заверши: `gh pr merge <N> --squash --delete-branch`, подтверди merged, отчитайся.
3. Если **rejected**: НЕ мёржить. Резюмируй, что runner должен изменить (из note), и предложи follow-up (`/autonomy:run` re-entry или ручная сессия на ветке).
4. Для `escalation`-записей: вердикт + note = продуктовое решение founder'а — запиши через `python scripts/autonomy/log_decision.py --phase <PNN> --kind escalated --fork "<fork>" --decision "<что founder выбрал>" --rationale "founder verdict: <note>"`, чтобы decision-trail остался полным.

## Guardrails
- Разрешай только записи, явно названные founder'ом. Никогда bulk-approve.
- Неизвестный/уже разрешённый RQ-ID → скажи (exit 4 из скрипта) — не гадай.
- Ack снимает ТОЛЬКО tripwire-паузу. Он НЕ подменяет `founder_signature` на гейте фазы (ADR-0017) — это разные checkpoint'ы.
