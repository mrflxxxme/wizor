# architect — workflows

## WF-1: Создание ADR

**Trigger:** planner/implementer/reviewer эскалировал architectural question.

1. Прочитай эскалацию: конкретный вопрос + контекст
2. Проверь существующие ADR — нет ли уже решения
3. Если нет → сформулируй Context, Decision, Consequences, Alternatives
4. Присвой следующий номер: `ADR-NNNN` (смотри последний в `.planning/decisions/`)
5. Запиши `.planning/decisions/ADR-NNNN-<slug>.md` (формат charter §8.3)
6. Хендофф → эскалирующему агенту: ссылка на ADR + краткий вывод

**Output:** `.planning/decisions/ADR-NNNN-<slug>.md`
**Handoff:** → эскалирующий агент (с решением)

---

## WF-2: Gate-проверка tier 4

**Trigger:** phase достигла exit-gate tier 4 (архитектура/биллинг/auto-fix/ПДн).

1. Прочитай gate-файл: `.planning/gates/<id>.md`
2. Проверь: все `hard_thresholds` выполнены? ADR-delta актуальна?
3. Если да → подпиши gate-вердикт (architect-подпись в gate-файле)
4. Если нет → открой blocker: укажи что именно не выполнено
5. Уведоми founder для final sign-off

**Output:** заполненный gate-файл (architect-вердикт)
**Handoff:** → founder (для подписи) / → planner (при blocker)

---

## WF-3: Арбитраж конфликта контрактов

**Trigger:** два агента имеют несовместимые ожидания от одного bounded-context.

1. Прочитай оба контракт-стаба + соответствующий ADR (если есть)
2. Определи: conflict in data ownership / API contract / event schema
3. Реши приоритет, задокументируй в ADR или обнови контракт-стаб
4. Хендофф к обоим агентам с решением

**Output:** обновлённый контракт-стаб или новый ADR
**Handoff:** → оба конфликтующих агента
