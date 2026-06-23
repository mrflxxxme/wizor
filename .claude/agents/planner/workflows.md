# planner — workflows

## WF-1: Планирование фазы (основной)

**Trigger:** founder открывает новую фазу из роадмапа.

1. Прочитай HEAD-SUMMARY phase-spec + STATUS.md + HANDOFF.md
2. Загрузи контракт-стабы затронутых bounded-context'ов (§7 charter)
3. Загрузи релевантные ADR (только по теме фазы, не все)
4. Декомпозируй в атомарные задачи: каждая ≤1 рабочий сессия
5. Для каждой задачи укажи: `id | role | tier | model | AC | contracts | depends_on | specialist?`
6. Проверь инварианты charter §6 на конфликты со scope
7. Запиши `.planning/PLAN.md` (pinned, не дата)
8. Хендофф → первому исполнителю (implementer или specialist)

**Output:** `.planning/PLAN.md`
**Handoff:** → backend-implementer / frontend-implementer / specialist

---

## WF-2: Ре-план (после ревизии)

**Trigger:** reviewer или architect вернул revision с незакрытыми issues.

1. Прочитай revision-файл + оригинальный PLAN.md
2. Определи: нужна новая задача или исправление AC существующей
3. Обнови PLAN.md: добавь задачу `<id>-fix` с явной ссылкой на revision
4. Хендофф → тому же implementer с уточнёнными AC

**Output:** обновлённый `.planning/PLAN.md`
**Handoff:** → implementer (fix-задача)

---

## WF-3: Специалист on-demand

**Trigger:** задача в phase-spec помечена как domain (GEO/crawler/LLM/CMS/152-ФЗ/devops).

1. Проверь: фаза касается домена специалиста?
2. Если да — добавь в PLAN.md задачу с `role: <specialist>` до implementer-задач
3. Specialist работает независимо, отдаёт артефакт → implementer интегрирует
4. Если специалист не нужен — 0 токенов (не спавни)

**Output:** задача в PLAN.md с `specialist: true`
**Handoff:** → specialist → implementer
