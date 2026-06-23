# reviewer — workflows

## WF-1: Ревью кода (основной)

**Trigger:** хендофф от implementer.

1. Прочитай хендофф: self-audit результат, diff, задача из PLAN.md
2. Запусти `checklists/pr-review.md` (все пункты)
3. Если `security_flag` или затронуты auth/billing/secrets/SQL/LLM → добавь security-линзу (charter §6 инварианты 1,3,4,8,9)
4. Запиши findings в `revisions/<phase>-cycle1-reviewer.md`: `severity | file:line | issue | required fix`
5. Если findings = 0 → verdict: approved → хендофф → verifier
6. Если findings > 0 → verdict: revision → хендофф → implementer

**Output:** `revisions/<phase>-cycleN-reviewer.md` или approved
**Handoff:** → implementer (revision) / → verifier (approved)

---

## WF-2: Цикл 2 (финальный)

**Trigger:** хендофф от implementer после цикла 1.

1. Прочитай только незакрытые findings из цикла 1
2. Проверь: устранены ли?
3. Если да → approved → verifier
4. Если нет → ESCALATE к architect (не цикл 3): запиши `revisions/<phase>-escalate.md` с summary незакрытых issues

**Output:** approved или escalation-файл
**Handoff:** → verifier (approved) / → architect (escalate)

---

## WF-3: Критический security issue

**Trigger:** обнаружен issue с severity: block (secrets в коде, CVSS-критический, read-only-нарушение).

1. Немедленно прерви обычный цикл
2. Запиши `revisions/<phase>-CRITICAL.md` с деталями
3. Хендофф → architect + founder одновременно
4. Не жди цикла — implementer должен фиксить на новом коммите

**Output:** `revisions/<phase>-CRITICAL.md`
**Handoff:** → architect + founder (параллельно)
