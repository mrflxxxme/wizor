# dpa-and-residency — self-audit (compliance-152fz-specialist)

## A. Резидентность (152-ФЗ, NFR-1)
- [ ] ПД только Yandex Cloud RF (Postgres, Redis, S3, backup, логи)
- [ ] Probe без ПДн → зарубежные ноды допустимы
- [ ] Контент клиента → RU-модели по умолчанию (NFR-3)

## B. Оператор ПД (перед prod)
- [ ] Уведомление РКН подано (pd.rkn.gov.ru, ст. 22 152-ФЗ)
- [ ] Политика обработки ПД опубликована; согласие пользователей реализовано
- [ ] DPA-шаблон (авто-правки) founder подписал

## C. DPA-активация auto-fix
- [ ] Факт акцепта в БД: `{tenant_id, dpa_version, accepted_at}`
- [ ] auto-fix заблокирован до `dpa_accepted = true`

## D. Audit log (FR-4.4)
- [ ] `wizor_audit_log` INSERT-only; retention ≥ 3 года
- [ ] Поля: patch_id, type, diff, applied_at, initiated_by, tenant_id

## E. Биллинг
- [ ] ЮKassa RF; чеки физ+юр (54-ФЗ); оферта опубликована
