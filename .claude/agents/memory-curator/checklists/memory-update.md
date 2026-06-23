# memory-update checklist (memory-curator)

Запускать при каждом шаге 8 цикла. Все пункты обязательны.

- [ ] **STATUS.md** обновлён: текущая фаза, статус, дата, следующий шаг
- [ ] **HANDOFF.md** ≤2 KB: содержит только необходимое для следующего агента/founder
- [ ] **JOURNAL.md** дополнен новой записью (формат: `YYYY-MM-DD | <phase> | <событие> | <агент>`)
- [ ] **JOURNAL rotation:** если >300 строк → архивировано в `_session-context/archive/JOURNAL-YYYY-Qn.md`
- [ ] **MEMORY-INDEX.md** обновлён (новые/изменённые строки с `updated` датой)
- [ ] **memory.md** дополнен patterns/pitfalls фазы (если есть новые)
- [ ] **Gate-frontmatter** `.planning/gates/<id>.md` заполнен: `actual`, `passed` для всех `hard_thresholds`
- [ ] **Аудит-архив:** `_session-context/AUDIT-*/` → `_session-context/archive/` (после merge)
- [ ] **README.md** статус-блок регенерирован (секция `## Статус`)
- [ ] Никаких secrets, полного кода или ПДн в owned-файлах

**Итог:** все 10 пунктов = done → хендофф → founder.
