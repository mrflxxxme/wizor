---
phase: P0
slug: discovery
title: "Discovery & De-risking (H1–H5)"
status: planned
tier: research
track: research
depends_on: []
gated_by: []
contracts: []
specialists: [geo-domain-expert, crawler-probe-specialist, compliance-152fz-specialist]
prd_refs: [§9.0, §16, §4.1]
model_default: opus
---
<!-- HEAD-SUMMARY (≤500т): Нулевая фаза, идёт параллельно P1–P5, нет продакшн-кода. Метод: 30 CustDev-интервью (15 SMB + 5 фрилансеров + 10 e-com) + 4 технических спайка. Результат: go/no-go по 5 гипотезам, блокирующим тяжёлый авто-фикс (P10). Все данные фиксируются в .planning/_meta/; gate формализован в .planning/gates/P0-to-heavy-autofix.md. -->

## Goal

Снять 5 рисковых гипотез (H1–H5) до начала дорогостоящей разработки CMS-коннекторов и авто-фикса. Работает **параллельно с P1–P5** — не блокирует базовую инфру. Результат: явное go/no-go для P10 (Auto track).

## In scope

- **30 CustDev-интервью:** 15 SMB-владельцев + 5 фрилансеров-маркетологов + 10 owner-операторов small e-com.
- **Технические спайки (4 шт.):** (1) time-to-citation для RU retrieval-поверхностей на новый контент; (2) прототип probe dual-geo (WP-тестовый сайт); (3) пробная подача DPA-условий реальным клиентам; (4) сравнение OSS vLLM vs GigaChat/YandexGPT для FAQ-генерации.
- **5 гипотез-гейтов:**
  - **H1.** Клиенты готовы дать API-доступ к сайту для авто-правок.
  - **H2.** Есть готовность платить за авто-имплементацию (vs ручная работа).
  - **H3.** Агентства готовы рассмотреть переход со Шпиониро/VisioBrand ради auto-fix.
  - **H4.** Реальный time-to-citation RU/retrieval-поверхностей на новый контент (замер спайком).
  - **H5.** Юр-готовность подписать DPA на авто-правки.
- Документирование находок в `.planning/_meta/discovery/`.
- Оформление gate `.planning/gates/P0-to-heavy-autofix.md` с `founder_signature`.

## Out of scope

- Любой продакшн-код.
- Разработка CMS-коннекторов (→ P10, gated_by P0).
- UX/дизайн, биллинг, онбординг.
- Формальная рыночная аналитика (→ уже в PRD §2).

## Functional requirements

- **FR-P0-1** (из §9.0): провести ≥30 интервью, охватить 3 целевых сегмента; каждое интервью зафиксировано структурированным шаблоном (job-to-be-done + willingness-to-pay + API-готовность + DPA-готовность).
- **FR-P0-2** (из §9.0 / H4): технический спайк измеряет time-to-citation для ≥2 RU retrieval-поверхностей (Яндекс Нейро/Алиса, GigaChat), публикуя контрольный тест-материал на WP-тестовом сайте и прогоняя probe через интервал.
- **FR-P0-3** (из §9.0 / H1+H5): пробная DPA-сессия с ≥5 реальными SMB — фиксация барьеров и акцептов.
- **FR-P0-4** (из §16): результаты H1–H5 формализованы как `passed` / `failed` / `pivoted` с evidence-ссылками; gate-файл подписан founder'ом.

## Acceptance criteria

- **AC-1:** ≥30 интервью завершены, артефакты в `.planning/_meta/discovery/interviews/`; минимум по 5 в каждом сегменте.
- **AC-2:** По каждой гипотезе (H1–H5) — явный вердикт (`go` / `no-go` / `conditional`) + 3+ цитаты-доказательства.
- **AC-3:** Спайк H4 даёт измеренное медианное значение time-to-citation для ≥2 поверхностей с n≥3 прогонами. Результат задокументирован в `.planning/_meta/discovery/spike-h4.md`.
- **AC-4:** Gate-файл `.planning/gates/P0-to-heavy-autofix.md` заполнен, статус `passed` или `blocked`; поле `founder_signature` непустое.
- **AC-5:** Если H1 или H5 = `no-go`, в gate зафиксирован pivot-сценарий (уточнение ICP / только Manual track / отсрочка P10).

## Contracts touched

Нет продакшн-контрактов. Единственный артефакт — gate-файл и discovery-документы в `.planning/`.

## Exit-gate

| Критерий | Порог | Файл-свидетель |
|---|---|---|
| Интервью проведены | ≥30 | `.planning/_meta/discovery/interviews/` (кол-во файлов) |
| Гипотезы H1–H5 вынесены | 5/5 с вердиктом | `.planning/gates/P0-to-heavy-autofix.md` |
| Founder-signature | непустое поле | gate-файл |
| Спайк H4 — медиана time-to-citation | задокументирована | `spike-h4.md` |

P10 (Auto track / CMS-коннекторы) **не стартует без `PASS`** по этому гейту.

## Decomposition hints for planner

1. Создать `.planning/gates/P0-to-heavy-autofix.md` (шаблон gate §8.5 charter) — день 1.
2. Разработать шаблон интервью (JTBD + H1/H2/H5 вопросы); согласовать с founder'ом.
3. Параллельно: рекрутинг респондентов + настройка WP-тестового сайта для спайка H4.
4. Нед. 1–4: интервью волна 1 (15 SMB) + спайк H4 (публикация контрольного контента + первые probe).
5. Нед. 5–6: интервью волна 2 (15 фрил+e-com) + DPA-сессии (H5) + спайк H1/H3.
6. Нед. 7–8: синтез, вердикты H1–H5, заполнение gate, founder-signature → передача в P10.
7. Привлечь `geo-domain-expert` для дизайна H4-спайка; `compliance-152fz-specialist` для DPA-тестирования (H5).
