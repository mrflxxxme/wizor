# reviewer — memory

**namespace:** `agent-memory:reviewer`
**owned files:** `revisions/<phase>-*.md`

## MUST-persist
- Паттерны повторяющихся findings (по типу и контексту)
- Список security-флагов, raised в прошлых фазах (не дублировать)
- Escalation-история: когда и почему эскалировали к architect

## MUST-NOT
- Полный diff кода
- Secrets / credentials (даже найденные — только pointer на файл:строку)
- Approval без запуска чек-листа

## Retrieval queries
- `tag:finding-pattern type:security` — security findings прошлых фаз
- `tag:escalation reason:<type>` — паттерны эскалаций
- `tag:cycle-count phase:<PNN>` — история циклов ревизии по фазе

## Pruning
revision-файлы старых фаз (status: merged) → архив (делает memory-curator). В namespace — только паттерны findings, не сами файлы.
