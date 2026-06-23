# frontend-implementer — workflows

## WF-1: Реализация frontend-задачи

**Trigger:** задача из PLAN.md с `role: frontend-implementer`.

1. Прочитай задачу: AC, contracts (API-контракт для страницы/компонента)
2. Загрузи контракт-стаб соответствующего backend-контекста
3. Если API STUB → создай mock-данные с `TODO: replace with real API`
4. Реализуй: Next.js page/route → React компоненты → shadcn/ui → API-вызовы (React Query/SWR)
5. Типизируй всё (TypeScript strict)
6. Прогони self-audit чек-лист
7. Атомарный коммит: `feat(<ctx>): <описание> Refs: PNN`
8. Хендофф → reviewer

**Output:** код в `src/`, тесты в `tests/`, коммит
**Handoff:** → reviewer (с self-audit: pass)

---

## WF-2: Fix после ревизии

**Trigger:** хендофф от reviewer с revision-файлом.

1. Прочитай findings, устрани по severity
2. Проверь: нет TS-ошибок, нет console.log PII
3. Self-audit + fix-коммит: `fix(<ctx>): address review cycle N Refs: PNN`
4. Хендофф → reviewer

**Output:** fix-коммит
**Handoff:** → reviewer

---

## WF-3: Tier 0 UI (no-auth PLG)

**Trigger:** задача P7 (Tier 0 Instant Audit) — публичный интерфейс.

1. Проверь: НИКАКИХ write-API вызовов (read-only-граница, инвариант §6.1)
2. Реализуй без auth (публичный route в Next.js)
3. Добавь явный TS-тип `ReadOnlyAuditResult` — не переиспользуй auth-типы
4. Self-audit с акцентом на инвариант 1 (charter §6)
5. Коммит + хендофф → reviewer

**Output:** публичная страница без write-операций
**Handoff:** → reviewer (с пометкой `tier0_public: true`)
