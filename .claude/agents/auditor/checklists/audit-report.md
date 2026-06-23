# audit-report template (auditor)

Файл: `_session-context/AUDIT-YYYY-MM-DD-<phase>/AUDIT-REPORT.md`

```markdown
# AUDIT-REPORT · <phase> · <YYYY-MM-DD>

**Вердикт:** PASS | PASS-WITH-FIXES | BLOCKED
**Tier фазы:** <T> → линз: <1|3|5>
**Линзы запущены:** корректность [· security · compliance [· тесты · архитектура]]

## Сводка находок

| id | линза | severity | file:line | issue | disposition |
|----|-------|----------|-----------|-------|-------------|
| F1 | | block/major/minor | | | fixed-in-loop / deferred-to-AC / blocked |

## Invariant check (10/10)
→ См. `checklists/invariant-checklist.md` — все 10 статусов здесь:
| inv | статус | комментарий |
|-----|--------|-------------|
| 1–10 | pass/fail | |

## Fix-цикл (если PASS-WITH-FIXES)
- F<N> отдан → <implementer> → re-verify → ожидается

## Deferred findings (founder-signed)
- F<N>: <описание> → AC <id> следующей фазы

## Вердикт обоснование
<1–3 предложения>
```

Посекционные файлы линз: `AUDIT-<phase>-lens-correctness.md`, `-security.md`, `-compliance.md`, `-tests.md`, `-architecture.md`
