# verifier — memory

**namespace:** `agent-memory:verifier`
**owned files:** `_session-context/VERIFY-<phase>-<ts>.md`

## MUST-persist
- Паттерны FAIL: какие AC чаще всего не выполняются и почему
- Exit-gate пороги прошлых фаз (для сравнения трендов)
- Случаи "AC non-verifiable" — для feedback к planner

## MUST-NOT
- Полный тест-вывод (только статус PASS/FAIL + pointer)
- Secrets в тест-данных
- Субъективные оценки ("почти готово") — только бинарный результат

## Retrieval queries
- `tag:fail-pattern phase:<PNN>` — паттерны неудач верификации
- `tag:exit-gate phase:<PNN>` — пороги прошлых гейтов
- `tag:non-verifiable-ac` — AC без измеримых критериев

## Pruning
VERIFY-файлы старых фаз → архив (memory-curator). Паттерны FAIL → держи компактно (gist + frequency).
