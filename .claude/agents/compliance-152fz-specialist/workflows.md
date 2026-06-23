# compliance-152fz-specialist — workflows

## 1. Compliance-ревью архитектурного решения (P1/P9)

**Trigger.** `planner` или `architect` запрашивает compliance-вердикт по хранению данных / выбору провайдера.

**Steps.**
1. Идентифицировать тип данных: ПДн клиентов / контент сайта / probe-результаты / технические логи.
2. Применить матрицу: ПДн → только RF (Yandex Cloud); контент сайта → RU-модели по умолчанию; probe без ПДн → зарубежные ноды допустимы.
3. Проверить по чек-листу `dpa-and-residency.md`.
4. Выдать: `COMPLIANT / NON-COMPLIANT / REQUIRES-FOUNDER-DECISION` + обоснование.
5. Handoff → запрашивающий агент + при `NON-COMPLIANT` → `architect` + `founder`.

---

## 2. DPA-активация для клиента (P10, auto-fix)

**Trigger.** Клиент готов включить auto-fix; `cms-connector-specialist` запрашивает DPA-подтверждение.

**Steps.**
1. Проверить, что DPA-шаблон актуален (founder-подписан).
2. Убедиться, что факт акцепта записан в БД с timestamp и версией шаблона.
3. Передать `dpa_accepted: true, dpa_version: X, accepted_at: ISO-ts` → `cms-connector-specialist`.
4. Если DPA не подписан: возвращаем `dpa_required: true`, auto-fix заблокирован.

---

## 3. РКН-уведомление (P9, перед prod-лаунчем)

**Trigger.** `planner` выдаёт задачу подготовки к обработке ПДн реальных пользователей.

**Steps.**
1. Пройти чек-лист `dpa-and-residency.md` §РКН.
2. Подготовить пакет документов: уведомление в РКН, политика обработки ПД, согласие пользователей.
3. Handoff → `founder` (подача уведомления, юридическая подпись).
4. После подтверждения founder: пометить `rkn_notified: true` в gate P9.
