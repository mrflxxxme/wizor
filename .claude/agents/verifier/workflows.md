# verifier — workflows

## WF-1: Acceptance verification (основной)

**Trigger:** хендофф от reviewer (verdict: approved).

1. Прочитай `checklists/gate-check.md`
2. Загрузи PLAN.md → список AC + live-gold-scope текущей задачи/фазы
3. Загрузи phase-spec exit-gate (количественные пороги)
4. Для каждого AC: запусти тест ИЛИ проверь артефакт. Нет теста = FAIL
5. **Авто-тесты:** unit + integration зелёные + coverage-гейт (ADR-0018)
6. **Live-gold (где возможно):** end-to-end против реальных сервисов с golden-набором. Невозможно → `deferred_live_gold` в отчёт + гейт (не тихо)
7. Проверь exit-gate пороги
8. Проверь: self-audit implementer = pass, review cycles завершены
9. Запиши `_session-context/VERIFY-<phase>-<ts>.md`: таблица AC→PASS/FAIL + `## Tests` + `## Live-gold` + итог

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
