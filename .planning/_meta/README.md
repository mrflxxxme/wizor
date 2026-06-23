# _meta/ — Справочная библиотека WIZOR

Короткие нормативные документы. **Точечный grep, не full-read.**

## Файлы

| Файл | Содержание | Когда читать |
|---|---|---|
| [`stack.md`](./stack.md) | Стек (backend/frontend/db/AI/infra), версии, фазы ввода | При выборе технологии |
| [`glossary.md`](./glossary.md) | Словарь продуктовых и харнесс-терминов | При незнакомом термине |
| [`conventions.md`](./conventions.md) | Код-стиль, tier-review, CI gates, DoD | При создании кода / PR |

## Quick-lookups

```bash
Grep("PostgreSQL", "_meta/stack.md")           # версия технологии
Grep("AI-Readiness Score", "_meta/glossary.md") # определение термина
Grep("Tier-based", "_meta/conventions.md")      # таблица апруверов
Grep("CI gates", "_meta/conventions.md")        # список CI-проверок
```

## Как агенты используют `_meta/`

1. Читай `MEMORY-INDEX.md` → ищи тег `stack` / `glossary` / `conventions`.
2. При попадании → грузи только нужный файл (или только HEAD-SUMMARY).
3. Грепай по конкретному термину — не читай файл целиком.
4. Не дублируй содержимое в phase-файлах — ставь cross-ref.

## Anti-patterns

- Full-read всех `_meta/*` в начале сессии.
- Дублирование версий/конвенций в phase-spec.
- Смена версии в `stack.md` без ADR.

## Что НЕ здесь

- `../contracts/` — bounded-context контракты
- `../decisions/` — ADR log
- `../gates/` — gate-файлы переходов
- `../OPEN-QUESTIONS.md`, `../PLACEHOLDERS.md`
