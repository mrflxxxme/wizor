---
gate: A-to-B
status: pending
opened_at: "2026-06-23"
closed_at: null
founder_signature: null

hard_thresholds:
  H_verified_uplift:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "≥ N сайтов с verified Readiness-uplift И наблюдаемым Visibility-сдвигом на ≥1 retrieval-поверхности (сдвиг вне полосы шума). N уточняется на момент оценки gate (ориентир источника: достаточно для 2–3 кейс-стади). Evidence: AUDIT-REPORT из фазы P8 + скриншоты-доказательства + Visibility-trend с CI."
  H_api_willingness_real:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "Готовность давать API-доступ и подписывать DPA ДОКАЗАНА на реальной выборке (≥ 3 сайта в Auto track с подписанным DPA и применёнными авто-правками). Evidence: DPA-файлы (анонимизированы) + audit log записей."
  H_autofix_reliability:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "Надёжность auto-fix: rollback-rate < 5% применённых правок; ноль инцидентов порчи production (corrupted HTML, broken layout, data loss). Evidence: сводный отчёт по всем применённым правкам из audit log; скриншоты rollback-тестов."
  H_mrr_signal:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "Пол MRR достигнут (конкретная цифра устанавливается основателем на мес. 6–8) И здоровый retention-сигнал (M3-retention ≥ целевого, уточняется). Evidence: выгрузка из ЮKassa + PostHog-дашборд retention."
  H_agency_interest:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "Входящий интерес ≥ 3–5 агентств: явно сформулированный запрос на white-label или agency-billing. Evidence: записи звонков / email-переписка / Telegram-переписка с агентствами."

deliverables:
  - id: D1
    name: "≥ 2 кейс-стади с verified Readiness-uplift опубликованы (vc.ru / Habr / Telegram)"
    status: pending
    owner: "founder + geo-domain-expert"
    notes: "Кейсы — конверсионный актив для B-трека"
  - id: D2
    name: "P7 (Tier 0 Instant Audit) в проде: публичный URL, рабочий PLG-вход"
    status: pending
    owner: "frontend-implementer + devops-infra-specialist"
    notes: ""
  - id: D3
    name: "P9 (Auth + billing + onboarding) в проде: ЮKassa, Keycloak, 3 тарифа, trial"
    status: pending
    owner: "backend-implementer + compliance-152fz-specialist"
    notes: ""
  - id: D4
    name: "P10 (Auto track: WP-коннектор + auto-fix + DPA) в проде и прошёл P0-gate"
    status: pending
    owner: "cms-connector-specialist + compliance-152fz-specialist"
    notes: "Зависит от P0-to-heavy-autofix gate"
  - id: D5
    name: "P8 (Верификация: re-crawl, deltas, evidence, alerts) в проде"
    status: pending
    owner: "crawler-probe-specialist"
    notes: ""
  - id: D6
    name: "PostHog-дашборд с North Star, воронкой Tier 0→Manual→Auto, M3-retention"
    status: pending
    owner: "backend-implementer + founder"
    notes: ""
  - id: D7
    name: "Pivot-дедлайн (мес. 9): явное решение go/pivot/stop задокументировано"
    status: pending
    owner: "founder"
    notes: "Если gate не достигнут к мес. 9 — обязательное pivot-решение"

adr_delta:
  created: []
  revised: []
  superseded: []

risks_delta:
  opened: []
  closed: []
  mitigated: []
  escalated: []
---

# Gate: Phase A → Phase B (Agency white-label)

## Назначение

Контрольная точка перехода с MVP/SMB self-serve (Phase A) на Agency white-label (Phase B). **Все 5 условий обязательны.** Переход без gate = нарушение evidence-gated scaling (доктрина §3).

**Pivot-дедлайн (мес. 9 фазы A):** если gate не достигнут — основатель принимает явное решение: pivot (в чистый agency-tool / сужение ICP) или stop.

## Hard thresholds (must-pass)

### H_verified_uplift — Доказанный uplift

≥ N сайтов с verified Readiness-uplift И наблюдаемым Visibility-сдвигом на ≥1 retrieval-поверхности. Сдвиг должен выходить за полосу шума (N≥5 прогонов + CI). Это North Star в действии.

### H_api_willingness_real — API/DPA доказаны на практике

Риск №1 (PRD §14) снят на реальных данных, а не только на custdev-интервью P0. ≥3 сайта в Auto track с подписанным DPA и применёнными авто-правками.

### H_autofix_reliability — Надёжность без инцидентов

rollback-rate < 5%, ноль порч production. Предпосылка для масштабирования на агентства (у них N клиентских сайтов — цена ошибки выше).

### H_mrr_signal — MRR и retention

Конкретные цифры устанавливает основатель на мес. 6–8 по динамике. Здоровый M3-retention подтверждает, что продукт удерживает (а не только привлекает).

### H_agency_interest — Входящий agency-интерес

≥ 3–5 агентств с явным запросом. Фаза B требует другого product + go-to-market; строить вслепую не нужно.

## Checklist

- [ ] Все 5 hard thresholds выполнены и задокументированы (evidence в `gates/evidence/A-to-B/`)
- [ ] 2–3 кейс-стади опубликованы
- [ ] PostHog-дашборд с North Star и воронкой работает
- [ ] P10 прошёл внутреннее QA и reliability-тест
- [ ] Основатель закрыл gate (подпись) или принял pivot-решение

## Что входит в Phase B (scope-preview)

- Multi-tenant: аккаунт агентства → N клиентских сайтов; роли agency admin / seo / client viewer.
- White-label кабинет (домен, лого, цвета).
- Agency-billing (счета, НДС, РФ-юрлицо).
- Bulk-операции (аудит/генерация 50 сайтов).
- Расширение CMS: Tilda, 1C-Битрикс, Modx, OpenCart.
- Sentiment-трекинг, competitive benchmarking, PDF/PPTX-отчёты.
- Партнёрская программа.

## Pivot-дедлайн

**Мес. 9 фазы A:** если gate не пройден — явное решение (ADR + JOURNAL запись):
- **Pivot вариант 1:** сужение ICP до чистого agency-tool (убрать SMB self-serve).
- **Pivot вариант 2:** repositioning на content API / embeddings (фаза C без B).
- **Stop:** если retention < порога и agency-интереса нет.

## Sign-off

- **Статус:** pending
- **Подпись основателя:** _pending_
- **Дата:** _pending_
- **Override justification** (только при status = waived): _n/a_
