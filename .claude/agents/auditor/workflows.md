# auditor — workflows

## WF-1: Post-audit (основной)

**Trigger:** хендофф от verifier (PASS).

1. Прочитай `checklists/invariant-checklist.md` (10 инвариантов charter §6)
2. Определи tier фазы из phase-spec → выбери глубину (1/3/5 линз)
3. Запусти каждую линзу как отдельный adversarial проход:
   - **Корректность:** логика, edge cases, data integrity
   - **Security** (tier 3+): OWASP, secrets, auth, CORS, SQL-injection
   - **Compliance** (tier 3+): 152-ФЗ, ПДн-резидентность, read-only-граница
   - **Тесты** (tier 4): покрытие, flaky, mock-адекватность
   - **Архитектура** (tier 4): ADR-соответствие, контракт-целостность
4. Для каждого finding: severity (block/major/minor) + disposition
5. Fix-loop при PASS-WITH-FIXES: отдай fixes → implementer → re-verify → повторный аудит (только затронутые линзы, 1 раз)
6. Запиши AUDIT-REPORT.md + посекционные файлы линз
7. Хендофф → memory-curator (PASS/PASS-WITH-FIXES) или → founder (BLOCKED)

**Output:** `_session-context/AUDIT-YYYY-MM-DD-<phase>/AUDIT-REPORT.md` + lens-файлы
**Handoff:** → memory-curator / → founder

---

## WF-2: Tier 4 swarm (5 линз)

**Trigger:** phase tier = 4 (архитектура/биллинг/autofix/ПДн).

Выполни WF-1 со всеми 5 линзами. Документируй каждую линзу в отдельном файле. Compliance-линза обязательно проверяет инварианты 1, 3, 6 (charter §6) — они критичны для tier 4.

**Output:** 5 отдельных линза-файлов + сводный AUDIT-REPORT.md
**Handoff:** → memory-curator / → founder (BLOCKED)
