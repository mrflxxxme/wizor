# self-audit checklist (frontend-implementer)

Запускать ДО хендоффа к reviewer. Все пункты = pass.

**Корректность**
- [ ] Все AC задачи выполнены (проверено по PLAN.md)
- [ ] Тесты написаны (unit + integration с mock API)
- [ ] `npm test` зелёный
- [ ] `npm run build` без TS-ошибок
- [ ] `npm run lint` чист

**Контракты**
- [ ] API-вызовы соответствуют контракт-стабу (типы совпадают)
- [ ] Если API STUB → mock-данные с `TODO: replace with real API`
- [ ] Нет прямых обращений к backend-эндпоинтам вне контракта

**Безопасность (charter §6)**
- [ ] Нет secrets / API-ключей в коде или публичных env-переменных (инвариант §6.9)
- [ ] Нет `console.log()` с ПДн или auth-токенами
- [ ] Read-only-граница: задача Tier 0 → НОЛЬ write-API вызовов (инвариант §6.1)
- [ ] CORS не расширялся без ADR

**Git**
- [ ] Коммит атомарный: 1 задача = 1 коммит
- [ ] Commit message: `feat(<ctx>): ... Refs: PNN`
- [ ] Нет закомментированного dead-кода
