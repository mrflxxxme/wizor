# gate-check checklist (verifier)

Запускать для каждой верификации. Результат: PASS или FAIL.

**Pre-flight**
- [ ] reviewer verdict = approved (хендофф получен)
- [ ] self-audit implementer = pass (указано в хендоффе)
- [ ] revision-файлы существуют в `revisions/`

**Acceptance criteria**
- [ ] Каждый AC из PLAN.md имеет соответствующий тест или проверяемый артефакт
- [ ] Нет AC без проверки (если нет теста → FAIL, не пропускать)
- [ ] Все тесты зелёные (`pytest` backend / `npm test` frontend)

**Exit-gate пороги** (из phase-spec)
- [ ] Все количественные пороги достигнуты (покрытие, latency, etc.)
- [ ] Пороги измерены, не оценены субъективно

**Итог**
- [ ] ВСЕ AC pass И ВСЕ пороги достигнуты → PASS
- [ ] Хотя бы одно FAIL → итог FAIL (без исключений)

**Output:** `_session-context/VERIFY-<phase>-<ts>.md` с таблицей: `| AC-id | description | status | evidence |`
