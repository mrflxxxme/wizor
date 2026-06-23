# self-audit checklist (backend-implementer)

Запускать ДО хендоффа к reviewer. Все пункты = pass.

**Корректность**
- [ ] Все AC задачи выполнены (проверено по PLAN.md)
- [ ] Тесты написаны (TDD: тест → реализация), не только happy-path
- [ ] `pytest` зелёный локально
- [ ] `mypy` / `ruff` без ошибок

**Контракты**
- [ ] API-контракт соблюдён (схема Pydantic соответствует контракт-стабу)
- [ ] `tenant_id` присутствует во всех multi-tenant операциях
- [ ] Input validation на каждом FastAPI endpoint (Pydantic модель)

**Безопасность (charter §6)**
- [ ] Нет secrets, credentials, env-значений в коде (инвариант §6.9)
- [ ] SQL только через ORM / parameterized queries (инвариант §6 смежный)
- [ ] Read-only-граница не нарушена (инвариант §6.1): если задача в Tier0/Manual track — нет write-операций

**Git**
- [ ] Коммит атомарный: 1 задача = 1 коммит
- [ ] Commit message: `feat(<ctx>): ... Refs: PNN`
- [ ] Нет `print()`, `console.log()` с ПДн/credentials
