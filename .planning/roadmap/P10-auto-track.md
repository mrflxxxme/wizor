---
phase: P10
slug: auto-track
title: "Auto track — WP-коннектор + auto-fix + trust-ladder + rollback + DPA"
status: planned
tier: 4
track: auto
depends_on: [P9]
gated_by: [P0]
contracts: [autofix, connectors]
specialists: [cms-connector-specialist, compliance-152fz-specialist, geo-domain-expert, frontend-implementer]
prd_refs: [EPIC-4/FR-4.1, EPIC-4/FR-4.2, EPIC-4/FR-4.3, EPIC-4/FR-4.4, EPIC-4/FR-4.5, EPIC-4/FR-4.6, EPIC-4/FR-4.7, §9.1, §3/принцип_4]
model_default: sonnet
---
<!-- HEAD-SUMMARY (≤500т): ⭐ Главный дифференциатор. AUTO-track: WP REST API + кастомный plugin → авто-применение машиночитаемого слоя (JSON-LD, robots.txt, llms.txt, IndexNow). Trust-ladder (дефолт ADR-0023): approval-gate → per-type opt-in сразу (без порога); FAQ никогда не auto. Append-only audit log + 1-click rollback + DPA-флоу. FAQ только через review-flow (staging → подтверждение → публикация). Frontend (ADR-0026): approve-очередь, FAQ-review, audit log/rollback, DPA-флоу. GATED_BY P0 (H1/H5 = go). 5-линзовый аудит (tier 4).

WP end-to-end (реальный сайт) — по природе live-only (ADR-0022). Каждый AC помечен классом. -->

## Goal

Реализовать Auto track — первый и главный дифференциатор WIZOR: авто-применение машиночитаемых правок на сайт клиента через WP-коннектор с полным audit trail, rollback и DPA-флоу. Только для Auto-mode тенантов с акцептованным DPA.

## In scope

- **WordPress-коннектор (FR-4.1):** кастомный WP-плагин (PHP, WordPress Plugin API) + WP REST API. Авто-применяет:
  - JSON-LD schema в `<head>` (через plugin hook).
  - robots.txt (правки AI-бот разрешений).
  - Генерация/публикация `llms.txt` / `llms-full.txt`.
  - IndexNow-пинг (уведомление Bing/Я.Вебмастер).
- **Trust-ladder (FR-4.2, дефолт ADR-0023):** по умолчанию каждое изменение в очередь на approve (`pending`); пользователь может включить `auto-apply` по конкретному типу машиночитаемой правки (per-type opt-in) **сразу, без порога «после N успешных approve»**. Видимый контент (FAQ) — **никогда** auto-apply.
- **FAQ review-flow (FR-4.3):** staging-предпросмотр → явное подтверждение пользователя → публикация. Без WP REST напрямую — только через review-модуль. Авто-публикация FAQ — физически заблокирована.
- **Append-only audit log (FR-4.4):** каждая правка: `fix_id`, `type`, `target_url`, `diff`, `applied_by`, `initiated_by`, `applied_at`, `status`. Записи неизменяемы.
- **Версионирование + 1-click rollback (FR-4.5):** перед применением сохраняется snapshot предыдущего состояния; rollback — один эндпоинт `POST /autofix/{id}/rollback`; откат тоже логируется.
- **DPA-флоу (FR-4.6):** до первой авто-правки — акцепт DPA (DataProcessingAgreement): форма → подпись → хранение (tenant_id, signed_at, version); auto-fix недоступен без DPA. Факт акцепта неизменяем.
- **Manual track совместимость (FR-4.7):** весь путь аудит→рекомендации→патчи работает без WP-коннектора; API/DPA требуются **только** для Auto track, не для входа в продукт.
- **Идемпотентность (NFR-4):** повторное применение одной правки → нет дублирования; вторичный вызов → `no-op` с `status: already_applied`.
- **Frontend (ADR-0026, UI-SPEC):** `approve-queue` (trust-ladder: pending-очередь + per-type opt-in toggle), `faq-review` (staging-предпросмотр → явное подтверждение → публикация; кнопки авто-публикации FAQ физически нет), `audit-log` (append-only журнал + 1-click rollback на записи), `dpa` (форма акцепта DPA до первой авто-правки, DpaGate). Все с честной индикацией статусов правок.

## Out of scope

- Tilda/Bitrix/Modx коннекторы (→ A.4 / фаза B).
- FAQ авто-публикация без review (явно запрещено, не только out-of-scope).
- Правки видимого текстового контента (заголовки, абзацы) в авто-режиме (→ фаза C или никогда).
- MCP-сервер (→ фаза C).
- Rollback cascades (цепочка зависимых правок) → фаза B/C.

## Functional requirements

- **FR-4.1** WordPress-коннектор (custom plugin → WP REST API): JSON-LD, robots.txt, llms.txt, IndexNow.
  - **AC PRD:** правки применяются на реальном WP-сайте; каждая обратима; повторное применение идемпотентно.
- **FR-4.2** Trust ladder: approval-gate по умолчанию; opt-in auto-apply по типу; видимый контент — никогда не авто.
  - **AC PRD:** видимый контент (FAQ) никогда не авто-применяется; только машиночитаемый слой → auto.
- **FR-4.3** FAQ review/merge-flow: staging-предпросмотр → подтверждение → публикация.
  - **AC PRD:** есть staging-предпросмотр; публикация только после явного подтверждения.
- **FR-4.4** Audit log: append-only, diff, timestamp, инициатор.
  - **AC PRD:** каждая правка с diff и timestamp; журнал неизменяем (append-only).
- **FR-4.5** Версионирование + 1-click rollback; откат тоже логируется.
  - **AC PRD:** любую применённую правку можно откатить одним действием; откат логируется.
- **FR-4.6** DPA-флоу: до первой авто-правки — акцепт; auto-fix недоступен без DPA; факт хранится.
  - **AC PRD:** auto-fix недоступен до акцепта DPA; факт акцепта хранится.
- **FR-4.7** Manual track без API: аудит→рекомендации→патчи без коннектора; DPA/API только для Auto track.
  - **AC PRD:** весь путь без write-доступа; DPA/API не требуются для входа в продукт.

## Acceptance criteria

- **AC-1 (WP end-to-end) [live-only]:** на тестовом WP-сайте: `POST /autofix/apply {fix_id}` → JSON-LD появился в `<head>` (Playwright verify); повторный вызов → `no-op`. Blocked до founder-owned test-WP.
- **AC-2 (trust-ladder default) [mock-verifiable]:** новый Auto-тенант без opt-in → фикс создаётся в `status: pending`, не применяется автоматически. Per-type opt-in доступен сразу (ADR-0023, без порога).
- **AC-3 (FAQ never auto) [mock-verifiable]:** попытка `auto-apply` фикса типа `faq_content` → 422 `cannot_auto_apply_visible_content`; тест фиксирует инвариант (см. §6 charter, инвариант 10).
- **AC-4 (audit log append-only) [mock-verifiable]:** после применения правки → `audit_log` запись создана с `diff`; попытка UPDATE/DELETE этой записи через ORM → ошибка/невозможно (DB constraint).
- **AC-5 (rollback) [live-only]:** `POST /autofix/{id}/rollback` → JSON-LD удалён из WP `<head>` (Playwright verify); в audit_log новая запись `action: rollback`. Blocked до test-WP.
- **AC-6 (DPA gate) [mock-verifiable]:** `POST /autofix/apply` без акцепта DPA → 403 `dpa_required`; после акцепта DPA → (доходит до connector). Проверяется без реального WP (mock-коннектор).
- **AC-7 (идемпотентность) [mock-verifiable]:** повторный `POST /autofix/apply` для уже применённого фикса → `{"status": "already_applied", "applied_at": "<ts>"}`, никаких изменений (mock-коннектор фиксирует no-op).
- **AC-8 (Manual track) [mock-verifiable]:** тенант без WP-коннектора → получает полный набор патчей в `copy-paste` режиме; `POST /autofix/apply` → 403 `connector_not_configured` (не `dpa_required`).
- **AC-9 (frontend auto-track, ADR-0026) [mock-verifiable]:** `approve-queue` (pending-список + per-type toggle), `faq-review` (staging→подтверждение, нет кнопки авто-публикации), `audit-log` + rollback-кнопка, `dpa` (DpaGate) рендерятся против mock-API (vitest/RTL); FAQ-review физически не имеет пути авто-публикации.
- **AC-10 (idempotency live) [live-only]:** повторное применение на реальном WP → сайт без дублирования (Playwright verify HTML идентичен). Blocked до test-WP.

## Contracts touched

- **`connectors` context:** `wp_connector_configs` (tenant_id, site_id, wp_url, api_key_encrypted, plugin_version); WP-плагин `wizor-connector.php` (PHP). Стаб → JIT.
- **`autofix` context:** `fix_queue` (fix_id, tenant_id, type, status, payload, scheduled_at); `audit_log` (append-only); `dpa_records` (tenant_id, signed_at, version, hash); `snapshots` (fix_id, before_state, after_state). API: `POST /apply`, `POST /rollback`, `GET /audit-log`, `POST /dpa/sign`.
- Зависит от: `entitlements` (P9 Auto mode gate), `recommendations.patch_artifacts` (P6), `crawler` (re-crawl verification P8).

## Exit-gate

| Критерий | Порог |
|---|---|
| P0 gate пройден | `P0-to-heavy-autofix.md` status=passed |
| Trust-ladder default pending | AC-2 (per-type opt-in без порога, ADR-0023) [mock] |
| FAQ never auto (инвариант §6.10) | AC-3 (422) [mock] |
| Audit log append-only | AC-4 (DB constraint) [mock] |
| DPA gate | AC-6 (403 без DPA) [mock] |
| Идемпотентность | AC-7 (no-op на повтор) [mock] |
| Manual track совместимость | AC-8 (403 connector_not_configured) [mock] |
| Frontend auto-track | AC-9 (approve/faq-review/audit-log/dpa) [mock] |
| WP end-to-end apply | AC-1 (JSON-LD в HEAD) [live-only, blocked: test-WP] |
| 1-click rollback | AC-5 (JSON-LD удалён + лог) [live-only, blocked: test-WP] |
| Идемпотентность live | AC-10 (no-op на реальном WP) [live-only, blocked: test-WP] |
| Аудит tier 4 | PASS (5 линз: correctness · security · compliance · tests · architecture) |

**Live-only AC блокированы до founder-ресурса** (ADR-0022): AC-1/5/10 требуют founder-owned test-WP. Mock-verifiable подмножество (AC-2/3/4/6/7/8/9 + tier-4 аудит) мёржится раньше; гейт фазы **и** P0-gate (H1/H5) — оба обязательны до закрытия.

## Decomposition hints for planner

1. `compliance-152fz-specialist` (Opus) проектирует DPA-флоу, audit-log constraint, DPA-хранение.
2. `cms-connector-specialist` (Sonnet) разрабатывает WP-плагин (`wizor-connector.php`): REST endpoints, JSON-LD hook, robots.txt, llms.txt writer, IndexNow ping.
3. `backend-implementer` реализует `AutofixOrchestrator`: fix_queue consumer → connector call → snapshot → audit_log.
4. `backend-implementer` реализует rollback-сервис + DPA-сервис.
5. `backend-implementer` реализует trust-ladder (per-type opt-in) + FAQ-gate (физическая блокировка).
6. `tester` пишет e2e (Playwright на WP): apply, rollback, idempotency, FAQ-gate.
7. `geo-domain-expert` (Opus) ревьюит: IndexNow корректен, llms.txt правильно генерируется как agent-infra (не citation-фактор).
8. Полный 5-линзовый аудит (tier 4) — особый фокус: auto-apply safety инварианты §6 charter (пп. 1, 3, 10).
