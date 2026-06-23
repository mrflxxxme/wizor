# verifier — workflows

## WF-1: Acceptance verification (основной)

**Trigger:** хендофф от reviewer (verdict: approved).

1. Прочитай `checklists/gate-check.md`
2. Загрузи PLAN.md → список AC текущей задачи/фазы
3. Загрузи phase-spec exit-gate (количественные пороги)
4. Для каждого AC: запусти тест ИЛИ проверь артефакт. Нет теста = FAIL
5. Проверь exit-gate пороги
6. Проверь: self-audit implementer = pass, review cycles завершены
7. Запиши `_session-context/VERIFY-<phase>-<ts>.md`: таблица AC → PASS/FAIL + итог

**Output:** `_session-context/VERIFY-<phase>-<ts>.md`
**Handoff:** → auditor (PASS) / → planner + founder (FAIL с таблицей)

---

## WF-2: Re-verify после fix

**Trigger:** planner запросил re-verify после fix-цикла.

1. Прочитай оригинальный VERIFY-файл — только FAIL строки
2. Перепроверь только эти AC
3. Если все закрыты → PASS → auditor
4. Если нет → FAIL (повторный) → founder (не planner — зацикливание)

**Output:** `_session-context/VERIFY-<phase>-<ts>-retry.md`
**Handoff:** → auditor (PASS) / → founder (повторный FAIL)
