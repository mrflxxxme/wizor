# cms-connector-specialist — workflows

## 1. WordPress-коннектор: первичная реализация (P10)

**Trigger.** `planner` выдаёт задачу P10, DPA-подтверждение получено от `compliance-152fz-specialist`.

**Steps.**
1. Реализовать WordPress custom plugin (PHP):
   - REST endpoint `POST /wizor/v1/apply-patch` (принимает patch-объект, применяет идемпотентно).
   - Версионирование: снапшот текущего состояния до правки (хранить в WP-options или custom table).
   - Endpoint `POST /wizor/v1/rollback/{patch_id}` (1-click rollback).
   - IndexNow-пинг после применения JSON-LD / robots.
2. Append-only audit log: таблица `wizor_audit_log` (INSERT только, нет UPDATE/DELETE).
3. Идемпотентность: хэш patch-объекта → если уже применён тот же хэш, вернуть `already_applied`.
4. Self-audit: проверить, что FAQ-патчи заблокированы на auto-apply (type=visible_content → reject).
5. Handoff → `backend-implementer` (WIZOR backend ↔ WP plugin API) + `compliance-152fz-specialist` (audit log ревью).

**Output.** `connectors/wordpress/wizor-plugin/` (PHP plugin) + API-схема.

---

## 2. Auto-apply машиночитаемой правки (runtime, P10)

**Trigger.** Backend WIZOR отправляет patch-объект на WP REST endpoint.

**Steps.**
1. Проверить DPA-флаг: `dpa_accepted = true` и `auto_apply_enabled` для данного типа.
2. Снапшот текущего состояния.
3. Применить патч: JSON-LD → `<head>`, robots.txt → overwrite, llms.txt → publish.
4. Записать в audit log: `{patch_id, type, diff, applied_at, initiated_by}`.
5. IndexNow-пинг (async).
6. Вернуть: `{status: applied, patch_id, rollback_url}`.

---

## 3. Rollback (1-click)

**Trigger.** Пользователь нажимает rollback в UI, backend вызывает WP endpoint.

**Steps.**
1. Найти снапшот по `patch_id`.
2. Восстановить предыдущее состояние (overwrite JSON-LD, robots.txt).
3. Записать в audit log: `{type: rollback, original_patch_id, rolled_back_at}`.
4. IndexNow-пинг обновлённого состояния.
5. Вернуть: `{status: rolled_back}`.
