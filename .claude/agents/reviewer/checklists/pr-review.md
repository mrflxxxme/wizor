# pr-review checklist (reviewer)

Запускать для каждого ревью. Findings → `revisions/<phase>-cycleN-reviewer.md`.

**Корректность**
- [ ] Все AC из PLAN.md реализованы (сверка с diff)
- [ ] Edge cases обработаны (null, empty, boundary)
- [ ] Нет race conditions / atomicity issues в concurrent операциях
- [ ] Тесты покрывают happy-path + основные failure-path

**Контракты**
- [ ] API-схема соответствует контракт-стабу
- [ ] `tenant_id` во всех multi-tenant операциях (backend)
- [ ] TypeScript типы соответствуют API-контракту (frontend)

**Security** (всегда; усиленно при security_flag)
- [ ] Нет secrets в коде (инвариант §6.9) — severity: block
- [ ] Input validation на каждой boundary (инвариант §6 смежный) — severity: block
- [ ] Read-only-граница не нарушена (инвариант §6.1) — severity: block
- [ ] SQL без string-interpolation (параметризованные запросы)
- [ ] CORS не расширён без ADR

**Качество**
- [ ] Self-audit implementer = pass (проверить хендофф)
- [ ] Нет dead-кода, TODO без ticket
- [ ] `print()` / `console.log()` с ПДн отсутствуют

**Format находок:** `| severity(block/major/minor) | file:line | issue | required fix |`
