# memory-curator — workflows

## WF-1: Memory-update после аудита (основной, шаг 8)

**Trigger:** хендофф от auditor (PASS или PASS-WITH-FIXES).

1. Прочитай `checklists/memory-update.md`
2. Прочитай AUDIT-REPORT.md + хендофф auditor
3. Обнови `.planning/STATUS.md` (rolling, только текущее состояние)
4. Обнови `.planning/HANDOFF.md` (≤2 KB, следующий агент читает это первым)
5. Append в `.planning/JOURNAL.md` (если >300 строк → ротация: архив + оставь 20 строк)
6. Обнови `.planning/MEMORY-INDEX.md` (новые/изменённые строки)
7. Append patterns/pitfalls в `.planning/memory.md`
8. Заполни gate-frontmatter `.planning/gates/<id>.md` (поля `actual`, `passed`)
9. Архивируй аудит: `_session-context/AUDIT-*/` → `_session-context/archive/` (после merge)
10. Регенерируй статус-блок в `README.md`
11. Хендофф → founder (готово к PR)

**Output:** все 8 обновлённых файлов
**Handoff:** → founder

---

## WF-2: Ротация JOURNAL

**Trigger:** JOURNAL.md >300 строк.

1. Скопируй текущий JOURNAL.md → `_session-context/archive/JOURNAL-YYYY-Qn.md`
2. Оставь в JOURNAL.md последние 20 строк + `<!-- archived: JOURNAL-YYYY-Qn.md -->`
3. Обнови MEMORY-INDEX.md: pointer на архив

**Output:** архивный файл + обновлённый JOURNAL.md

---

## WF-3: Обновление MEMORY-INDEX

**Trigger:** новый ADR / новый контракт / новый паттерн (от architect или фаза завершена).

1. Прочитай новый документ
2. Создай/обнови строку в MEMORY-INDEX.md: `| tag | topic | pointer | gist (1 строка) | updated |`
3. НЕ храни полный текст — только gist + ссылка

**Output:** обновлённый `.planning/MEMORY-INDEX.md`
