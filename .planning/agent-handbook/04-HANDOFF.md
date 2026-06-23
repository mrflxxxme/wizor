<!-- HEAD-SUMMARY (≤500т): Компактный handoff-блок (charter §8.6), rolling-снапшот HANDOFF.md (≤2 KB), протокол возобновления работы после паузы/смены сессии. -->

# 04-HANDOFF — протокол передачи состояния

## Зачем handoff

Любая смена агента, пауза или конец сессии без handoff = потеря контекста. Хороший handoff позволяет следующей сессии стартовать за 2 минуты, не перечитывая всю историю.

## Компактный handoff-блок (charter §8.6)

Формат — всегда Markdown, никогда CloudEvents JSON. Вставляй в HANDOFF.md и в описание PR:

```
### HANDOFF <from> → <to> · <phase> · <ISO-ts>
- task: <одна строка — что делалось>
- did: <ключевое сделанное — файлы / коммиты / решения>
- artifacts: [путь/к/файлу, ...]
- contracts_touched: [ctx1, ctx2]
- self_audit: pass | fail  (+ ссылка на checklist-файл)
- next: <следующее действие>
- escalate: none | <причина + вопрос к founder>
```

**Пример:**
```
### HANDOFF backend-implementer → reviewer · P2-crawler · 2026-06-23T14:32Z
- task: реализовать endpoint POST /api/v1/audit/crawl
- did: src/crawler/routes.py, src/crawler/service.py, tests/test_crawl.py; коммит abc1234
- artifacts: [src/crawler/routes.py, src/crawler/service.py]
- contracts_touched: [crawler, scoring]
- self_audit: pass (checklists/backend-self-audit.md)
- next: reviewer проверяет по чек-листу контракт crawler
- escalate: none
```

## Rolling-снапшот HANDOFF.md

Файл `.planning/HANDOFF.md` — **скользящий снапшот**, не архив. Лимит: **≤ 2 KB**.

Содержит только:
- Последний HANDOFF-блок (последняя завершённая роль)
- Что сейчас in-progress (задача + исполнитель)
- Ближайший next-step
- Активные блокеры / эскалации

История хендоффов уходит в `_session-context/archive/` — `memory-curator` ротирует.

## Протокол возобновления (resume)

При старте новой сессии после паузы:

```
1. Read .planning/STATUS.md        → активная фаза, блокеры
2. Read .planning/HANDOFF.md       → что оставлено, что next
3. Read .planning/MEMORY-INDEX.md  → если нужны дополнительные темы
4. Read phase-spec PNN             → только если меняется задача
```

**Не нужно:** перечитывать charter (уже известен), весь JOURNAL, архив аудитов.

## Что обязательно писать в хендофф

**MUST-persist** (через `memory-curator`):
- Принятые решения с обоснованием
- Паттерны и подводные камни, обнаруженные в фазе
- Статус гейтов (что passed / что pending)
- Активные эскалации с форматом из `03-ESCALATION.md`

**MUST-NOT** включать в HANDOFF.md:
- Полный код (только ссылки на файлы)
- Секреты / credentials
- Чужой контент (только ссылки)
- Исторические хендоффы (уже в archive/)

## Exit-ritual перед merge PR

Перед тем как PR уходит на аппрув founder:

1. `memory-curator` дописывает запись в `JOURNAL.md`
2. `memory-curator` обновляет `HANDOFF.md` снапшот
3. `memory-curator` регенерирует статус-блок в `README.md`
4. Оба файла упомянуты в описании PR

Без этих шагов review-gate блокирует мердж (см. `05-PR-WORKFLOW.md`).
