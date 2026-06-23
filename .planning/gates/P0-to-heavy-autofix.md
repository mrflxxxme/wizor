---
gate: P0-to-heavy-autofix
status: pending
opened_at: "2026-06-23"
closed_at: null
founder_signature: null

hard_thresholds:
  H1_api_willingness:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "H1: ≥ 8 из 15 SMB-владельцев (custdev-интервью) выражают готовность предоставить API-доступ к сайту для авто-правок. Метод: 30 customer-development интервью (15 SMB + 5 фрилансеров + 10 owner-операторов e-com). Evidence: сводная таблица интервью + дословные цитаты + score-breakdown."
  H2_willingness_to_pay:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "H2: ≥ 6 из 30 респондентов выражают готовность платить за авто-имплементацию (vs ручная работа) по ориентировочным тарифам (5 990–14 990 ₽/мес). Evidence: записи/транскрипты интервью с явным ответом на вопрос WTP."
  H3_agency_switchover:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "H3: ≥ 2 SEO/SERM-агентства выражают конкретный интерес к переходу со Шпиониро/VisioBrand ради auto-fix-возможностей. Evidence: записи звонков + email/Telegram-переписка с Agency-контактами."
  H4_time_to_citation:
    target: "measured"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "H4: Замерен реальный time-to-citation для RU-retrieval-поверхностей (Яндекс Нейро/Алиса) на новый контент/schema — технический спайк. Результат: медиана и диапазон (дней). Evidence: CSV с замерами спайка (≥10 тестовых страниц, ≥3 прогона каждой)."
  H5_dpa_readiness:
    target: "proven"
    actual: null
    passed: null
    evidence_url: null
    measured_at: null
    description: "H5: ≥ 5 респондентов из целевого ICP (SMB) готовы подписать DPA на авто-правки после ознакомления с примером соглашения. Evidence: заполненные формы согласия-в-принципе / интервью-транскрипты с явным ответом."

deliverables:
  - id: D1
    name: "30 customer-development интервью завершены (15 SMB + 5 фрил + 10 e-com)"
    status: pending
    owner: "founder"
    notes: "Метод: звонки Zoom/Telegram, 30–45 мин, скрипт вопросов по H1–H5"
  - id: D2
    name: "Сводная таблица интервью с оценкой H1–H5 по каждому респонденту"
    status: pending
    owner: "founder + geo-domain-expert"
    notes: "Формат: Google Sheet / Markdown-таблица; анонимизирована для privacy"
  - id: D3
    name: "Технический спайк time-to-citation (H4): ≥10 тестовых страниц, ≥3 прогона"
    status: pending
    owner: "crawler-probe-specialist"
    notes: "Параллельно с custdev; результат — CSV + REPORT.md в .planning/gates/evidence/P0/"
  - id: D4
    name: "Черновик DPA-соглашения (согласован с compliance-152fz-specialist)"
    status: pending
    owner: "compliance-152fz-specialist + founder"
    notes: "Нужен для H5 (показывать респондентам)"
  - id: D5
    name: "Go/no-go решение основателя по тяжёлому auto-fix (P10)"
    status: pending
    owner: "founder"
    notes: "Документируется как ADR + запись в JOURNAL"

adr_delta:
  created: []
  revised: []
  superseded: []

risks_delta:
  opened:
    - R-1
    - R-2
  closed: []
  mitigated: []
  escalated: []
---

# Gate: P0 → Тяжёлый auto-fix (P10)

## Назначение

Этот gate блокирует запуск **P10 (Auto track: WP-коннектор + auto-fix + trust-ladder + rollback + DPA)** до тех пор, пока 5 рисковых гипотез не подтверждены на реальных данных (PRD §9.0, §8).

Параллельно с P0 строятся фазы P1–P5 (инфра, краулер, скоринг, LLM-router, probe) — они нужны при любом исходе. P10 стартует **только** после прохождения этого gate.

## Hard thresholds (must-pass)

### H1 — Готовность дать API-доступ

30 customer-development интервью (нед. 0–8). ≥ 8/15 SMB-владельцев выражают готовность предоставить API-доступ для авто-правок. Это риск №1 тезиса (PRD §14).

**Митигация при fail:** Manual track монетизируется без API — продукт выживает; Auto track откладывается или перепозиционируется.

### H2 — Willingness-to-pay за авто-имплементацию

≥ 6/30 респондентов готовы платить по ориентировочным тарифам. Разделяет «интересно» и «заплачу».

### H3 — Интерес агентств

≥ 2 SEO/SERM-агентства с конкретным сигналом переключения. Валидирует B-трек до его старта.

### H4 — Time-to-citation (технический спайк)

Измеренная медиана и диапазон для Яндекс Нейро/Алисы. Нужна для дизайна trial-окна (NFR-8: ≥21–30 дн) и для позиционирования honest forecast.

### H5 — DPA-готовность

≥ 5 ICP-респондентов готовы подписать DPA. Без этого trust-ladder и audit log не имеют юр-основания.

## Checklist

- [ ] Скрипт интервью утверждён (вопросы покрывают H1–H5)
- [ ] 30 интервью проведены и транскрибированы
- [ ] Черновик DPA передан юристу / compliance-specialist и согласован
- [ ] Технический спайк H4 выполнен; CSV + отчёт в `evidence/P0/`
- [ ] Сводная таблица оценок H1–H5 заполнена
- [ ] Основатель принял go/no-go решение, задокументировал ADR
- [ ] Gate-статус обновлён `memory-curator`

## Founder decision area

_(Founder заполняет при оценке gate: какие гипотезы прошли / упали; как это меняет scope P10; ADR-номер решения.)_

## Sign-off

- **Статус:** pending
- **Подпись основателя:** _pending_
- **Дата:** _pending_
