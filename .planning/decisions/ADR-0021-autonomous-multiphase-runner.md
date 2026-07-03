---
id: ADR-0021
title: autonomous-multiphase-runner
status: accepted
date: 2026-07-03
supersedes: []
amends: [ADR-0017, ADR-0018, ADR-0009]
---
<!-- HEAD-SUMMARY (≤500т): Порт ORIION ADR-037 в WIZOR. Переходим на автономный многофазный runner, где СТРОГИЙ ГЕЙТ-СТЕК — merge-authority, а не глаза founder'а; founder в петле только на исключениях. 8 решений D1–D8: D1 полная автономия мёржа + D2 задняя растяжка (8 tripwire-категорий → 1-клик ack) + D3 коммит-привязанный evidence (усиливает live-gold ADR-0018 до неподделываемого) + D4 передняя растяжка (эскалация только продукт/рынок + tripwire) + D5 judge-панель на широких форках (судья=auditor) + D6 runner /autonomy:run (9-шаговый цикл сцеплен) + D7 self-healing (auto-revert + fix-loop) + D8 notify (push + RUN-QUEUE + Telegram). Машина ставится ВЫКЛЮЧЕННОЙ — вооружается founder'ом (settings/hook snippets + branch protection). Реализация: .claude/autonomy/ + scripts/autonomy/ + .claude/commands/autonomy/. -->

## Context

Харнесс WIZOR (charter 9-шаговый цикл, ADR-0017 gate-only автономия, ADR-0018 live-gold) до сих пор исполнялся бы **вручную, одной сессией на фазу**: founder выбирает scope, «приступай», агент имплементит + аудит-сабагенты, local CI, PR — и хотя ADR-0017 упразднил per-PR аппрув, оркестрация цикла осталась ручной и без исполняемых предохранителей (ADR-0020 добавил slash-команды/role-loader, но не автономный runner). ORIION прошёл этот же путь и решил его через ADR-037: автономный runner + gate-authority merge. Founder WIZOR (интервью 2026-07-03) выбрал: интегрировать автономную методологию ORIION полноценно, дать проекту реальную автономность с минимальным включением, сохраняя lean (ADR-0001).

Три силы: (1) скорость — сессия-на-фазу = налог ре-bootstrap; (2) время founder'а — в петле ≥3 раза за фазу; (3) автономность решений — агенты сами находят *оптимальные* решения, а не собирают мнение по каждому форку.

Constraint, который нельзя нарушить (как у ORIION): **«не потерять стабильность».** Founder выходит из merge-петли только при условии, что security/integrity/152-ФЗ/local-run гейты станут *строже*, а не слабее. Доверие переносится с глаз founder'а на верифицируемую машину.

## Decision

Переходим на **автономный многофазный runner, где строгий гейт-стек — merge-authority, а не глаза founder'а**; founder в петле только на исключениях (узкие растяжки + продукт-эскалации + застрявшие гейты). Восемь нормативных решений (порт ADR-037, адаптация к WIZOR-ростеру/инвариантам):

**D1 — Review posture: полная автономия мёржа на всех тирах.** Операционализирует ADR-0017 (человек — только на гейте фазы). Условие активации: D2–D3 построены и зелены *до* включения runner'а.

**D2 — Задняя растяжка: узкий список категорий → 1-клик ack.** Авто-мёрж всё зелёное, КРОМЕ diff'ов, задевающих 8 категорий (`.claude/autonomy/tripwire.yaml`): миграции по существующим таблицам/RLS · auth/IAM/tenancy · billing · секреты/ключи/crypto · слом публичных контрактов · **auto-fix write-путь** · **probe-geo egress** · **ПДн/152-ФЗ/DPA**. Последние три — WIZOR-специфичные (charter §6 инв. 1/3/4/6), которых нет в ORIION: наш уникальный риск-surface. Детект по path-глобам; ~95% фаз мёржатся автономно.

**D3 — Целостность гейтов: evidence-артефакт + CI-verify.** Гейты, которые GitHub CI прогнать не может (funded live-gold crawl/probe, Docker-интеграция, адверсариальный аудит), обязаны эмитить коммит-привязанный `evidence/<gate>.json` (`head_sha` == PR head). Job `evidence.yml` ассертит существование + свежесть + `verdict==PASS`. **Усиливает ADR-0018**: live-gold перестаёт держаться на честном слове — становится неподделываемым на мёрже.

**D4 — Передняя растяжка: эскалация только на продукт/рынок + необратимое.** Агент владеет всеми impl+arch форками (пишет ADR + логирует в DECISIONS-LOG). Эскалирует к founder только: (1) продуктово-рыночное (ЦА/цена/scope/бренд/152-ФЗ-стратегия — территория founder ADR-0017 §5), (2) tripwire-категории D2. Зеркало задней растяжки (`escalation-policy.md`).

**D5 — Оптимальность: judge-панель на широких форках.** Большинство задач — один проход. Широкие форки (архитектура/алгоритм/схема, высокий blast radius) → N подходов → роль **`auditor`** (не `evaluator` — в лёгком ростере WIZOR судья = auditor, charter §3/§6) ранжирует по рубрике корректность→безопасность/compliance→простота→стоимость→перформанс → winner + graft (`judge-panel.md`).

**D6 — Runner: секвенциальная цепь + opt-in worktree-параллелизм.** `/autonomy:run` крутит 9-шаговый цикл charter §4 сцеплено (scope→discuss→plan→domain→implement→review→verify→audit→memory→PR→auto-merge|ack→next) до эскалации/ack/застрявшего гейта/пустой очереди. Независимые треки — параллельно в отдельных worktree (opt-in, макс 2, мёржи сериализованы).

**D7 — Rollback: авто-реверт регрессии + автономный fix-loop + уведомление.** Авто-смёрженная фаза позже роняет гейт на main → runner авто-ревертит (main зелёный по построению → реверт обратим), спавнит fix-цикл (макс 3), **уведомляет founder о реверте** (`/autonomy:heal`, `check_main_health.py`).

**D8 — Notify: push + RUN-QUEUE + Telegram.** 5 interrupt-событий (ack / product-эскалация / реверт / застрявший гейт / run завершён): `PushNotification` + `.planning/_session-context/RUN-QUEUE.md` (единое окно founder'а) + опц. Telegram phone-ack (`notify.json`).

**Порядок сборки (предохранители ДО автономии):** Блок A (рельсы: evidence + tripwire + хук + branch protection) → B (фронт: escalation + judge + decisions-log) → C (runner + auto-merge + RUN-QUEUE + notify + role-loader) → D (self-healing) → E (параллелизм). Машина ставится **выключенной**; вооружается founder'ом (settings/hook-snippets + branch protection — Claude не self-install'ит execution-authority).

## Consequences

- ✅ **Скорость:** цикл фазы теряет founder-точки и налог ре-bootstrap; фазы сцепляются в одной сессии.
- ✅ **Верифицируемая целостность:** D3 делает live-gold (ADR-0018) неподделываемым; main зелёный по построению (D7). Стабильность растёт, а не падает — прямое исполнение constraint'а founder'а.
- ✅ **Audit-trail:** evidence-артефакты + DECISIONS-LOG + RUN-QUEUE = полная картина «что случилось, пока меня не было» для post-hoc founder-аудита.
- ✅ **WIZOR-специфичная безопасность:** tripwire покрывает наш уникальный необратимый surface (auto-fix на чужой prod, RU-IP probe-утечка, ПДн) — жёстче ORIION.
- ⚠️ **Стоимость:** автономный прогон + judge-панель жгут токены; runner уважает `cost-budget.yaml` (charter §3.4) + per-run cap.
- ⚠️ **Риск авто-реверта:** может ошибиться; смягчается обратимостью реверта + немедленным уведомлением (D7/D8) + sanity-check атрибуции.
- ⚠️ **Runtime-разрыв:** `classify_tripwire.py` использует PyYAML (backend-venv/uv) — вооружить premerge-хук только после проверки окружения (BUILD-PLAN §Разрывы).

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| Полное ревью, только фронт быстрее | доверие к гейтам не меняется | founder в петле каждую фазу | не бьёт в главный налог — время founder'а |
| Ноль растяжки — всё авто | макс скорость | необратимое (данные/деньги/секреты/ПДн/чужой prod) без предохранителя | против «не потерять стабильность» |
| CI твёрдый, локальные self-report | проще | live/integration на честном слове | дыра целостности под автономией — неприемлемо (152-ФЗ) |
| Всегда multi-approach + judge | макс качество | 2–3× токены/фазу | конфликт с «быстрее» + cost-budget |
| Фоновый cron-runner | макс hands-off | Docker + funded-.env под founder-контролем ломают live-гейты | против стабильности; отложено |
| Тяжёлый ORIION 1:1 (CloudEvents, 11 ролей) | верность | раздувает контекст | founder выбрал lean (ADR-0001); адаптируем под 14-ростер WIZOR |

## Links

- **Порт:** ORIION `ADR-037-autonomous-multiphase-runner` (8 решений D1–D8; адаптировано к WIZOR-ростеру/§6-инвариантам/PNN-фазам).
- **Amends:** ADR-0017 (gate-only автономия → D1 операционализация + D2/D4 растяжки), ADR-0018 (live-gold → D3 коммит-привязка), ADR-0009 (PR-на-фазу → auto-merge-on-green).
- **Использует:** ADR-0020 (executable layer: role-loader D6, slash-команды), ADR-0005 (риск-тир аудит → judge-панель D5 через `auditor`), ADR-0002 (14-ростер).
- Charter: `BUILD-CHARTER.md §4` (9-шаговый цикл), `§6` (стоячие инварианты → tripwire/escalation), `§11` (автономия).
- Runtime: `.claude/autonomy/` (конфиг+доки) · `scripts/autonomy/` (8 скриптов) · `.claude/commands/autonomy/` (4 команды).
- Cost: `.claude/agents/_shared/cost-budget.yaml` (charter §3.4 per-run cap).
