# memory-curator — memory

**namespace:** `agent-memory:memory-curator`
**owned files:** `.planning/STATUS.md`; `.planning/HANDOFF.md`; `.planning/JOURNAL.md`; `.planning/MEMORY-INDEX.md`; `.planning/memory.md`; `_session-context/archive/`; `README.md` (статус-блок)

## MUST-persist
- Метаданные последней ротации JOURNAL (дата + имя архив-файла)
- Список gate-файлов с незаполненными полями (pending)
- Паттерны ошибок других агентов (для улучшения их профилей)

## MUST-NOT
- Secrets, credentials, ПДн
- Полный код или diff (только pointer)
- Чужой контент (только pointer на источник)
- Дублирование MEMORY-INDEX в namespace (namespace ↔ INDEX в sync)

## Retrieval queries
- `tag:rotation-history` — история ротаций JOURNAL
- `tag:gate-pending` — незакрытые gate-поля
- `tag:memory-pattern agent:<role>` — паттерны от агентов

## Pruning
Сам namespace — минимален. MEMORY-INDEX — единственный каталог. Удаляй из namespace то, что уже в MEMORY-INDEX с pointer. Ротируй каждый квартал или при >50 записях.
