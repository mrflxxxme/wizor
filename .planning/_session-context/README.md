# _session-context/ — Пост-аудиты и контекст сессий

Эфемерные рабочие файлы и обязательные пост-аудит отчёты (чартер §6).

## Структура

```
_session-context/
├── AUDIT-<date>-<phase>/       ← пост-аудит конкретной фазы
│   ├── AUDIT-REPORT.md         ← вердикт + таблица диспозиции находок
│   ├── lens-correctness.md     ← (Tier 3+)
│   ├── lens-security.md        ← (Tier 3+)
│   ├── lens-compliance.md      ← (Tier 3+)
│   ├── lens-tests.md           ← (Tier 4)
│   └── lens-architecture.md   ← (Tier 4)
└── archive/                    ← старые аудиты после merge
```

## Конвенция AUDIT-* (чартер §6)

**Создаёт:** `auditor`/Opus (шаг 7 цикла). **Обязательно для каждой фазы.**

**Имя:** `AUDIT-YYYY-MM-DD-<phase>` (пример: `AUDIT-2026-08-01-P2`).

**Глубина по Tier:**
- Tier 1–2 → только AUDIT-REPORT.md (1 линза)
- Tier 3 → + 3 линзы: correctness · security · compliance
- Tier 4 → + 5 линз: + tests · architecture

**AUDIT-REPORT.md содержит:**
- Вердикт: `PASS` / `PASS-WITH-FIXES` / `BLOCKED`
- Таблица: `| Находка | Severity | Диспозиция | Статус |` (диспозиция: fixed-in-loop / deferred-to-AC / blocked)
- Статус каждого из 10 стоячих инвариантов (чартер §6)

## Архивирование

После merge PR → `memory-curator` (шаг 8 цикла) перемещает:
```
AUDIT-2026-08-01-P2/  →  archive/AUDIT-2026-08-01-P2/
```

STATUS.md, HANDOFF.md, JOURNAL.md живут в корне `.planning/` — не здесь.
