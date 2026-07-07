<!-- HEAD-SUMMARY (≤500т): Инвентарь экранов веб-кабинета и публичных страниц MVP WIZOR — спецификация словами (без макетов/CSS) для frontend-implementer (Next.js 15 / React 19 / TS strict / Tailwind / shadcn/ui). Публичные: landing (URL-инпут) + Tier0 result (async, два порога). Кабинет: dashboard, recommendations, competitive gap, visibility trends, alerts, approve queue, FAQ review, audit log/rollback, DPA, onboarding, billing, prompt-editor, login/register. Компонентная база (ScoreGauge, PatchCard, TrendChart с CI-band, ForecastBadge…) + соответствие фазам P6–P10. Инвариант: нигде гарантированного Visibility-%, всегда диапазон+disclaimer; «нет ложных побед» внутри CI. -->

# UI-SPEC — инвентарь экранов веб-кабинета и публичных страниц (MVP)

> Спецификация СЛОВАМИ (не пиксельный макет). Достаточна, чтобы `frontend-implementer` собирал UI пофазно и однозначно. Детали каждого компонента — JIT при планировании фазы.
> Конвенция языка (CLAUDE.md): нарратив — русский; идентификаторы, роуты, поля, имена компонентов — английский.

---

## Принципы

1. **Rendering.** Публичные страницы (`landing`, `Tier0 result`) — SSR/ISR (быстрый первый экран; landing индексируем, result — `noindex`). Кабинет — server components для каркаса + client components для интерактива; данные через TanStack Query поверх JWT.
2. **База — shadcn/ui** поверх Tailwind, без собственной дизайн-системы: `Button`, `Card`, `Dialog`, `Table`, `Tabs`, `Badge`, `Progress`, `Toast`, `Switch`, `Form` (React Hook Form + Zod), `Skeleton`, `Alert`. Графики — Recharts.
3. **PostHog** на ключевых действиях. Имена событий — КОНТРАКТ с backend (`frontend/lib/analytics.ts::NorthStarEvent` ↔ `backend/.../posthog.py`), менять синхронно. Есть: `page_viewed`, `audit_started`, `score_calculated`, `fix_applied`. Фазовые (`tier0_*`, `user_registered`, `trial_started`, `first_fix_applied`, `converted_to_paid`) добавляются в тот же контракт.
4. **Честность прогноза (инвариант §6.2 charter, FR-3.5).** Нигде не показывается гарантированный Visibility-%. Вероятностный прогноз — ТОЛЬКО диапазон + confidence + disclaimer (`ForecastBadge`). Детерминированная Readiness-проекция («Score X→Y») — точное число допустимо. Тренды — с полосой шума (CI-band); улучшение НЕ заявляется, пока Δ внутри полосы (`is_significant=false`).
5. **RU-интерфейс.** Весь видимый текст, даты/числа — ru-RU. Disclaimer и ошибки — человекочитаемые.
6. **Multi-tenant.** Запросы кабинета неявно скоупятся `tenant_id` из JWT-claims; UI никогда не принимает `tenant_id` из инпута. Активный `site_id` — в роуте.

---

## Карта экранов (инвентарь)

| Экран | Роут | Auth | Фаза | Назначение |
|---|---|---|---|---|
| Landing (Instant Audit) | `/` | no-auth | P7 | URL-инпут → запуск Tier0-аудита, PLG-вход |
| Tier0 result | `/audit/[jobId]` | no-auth | P7 | Async-результат (два порога загрузки) + CTA на регистрацию |
| Login | `/login` | no-auth | P9 | Вход через Keycloak OIDC |
| Register | `/register` | no-auth | P9 | Регистрация через Keycloak OIDC, старт trial |
| Onboarding wizard | `/app/onboarding` | auth | P9 | 4 шага: сайт → аудит → промпты → первая правка (aha) |
| Dashboard | `/app` | auth | P6 | AI-Readiness Score + компоненты + сводка сайта |
| Recommendations | `/app/sites/[siteId]/recommendations` | auth | P6 | Прио-список фиксов + copy-paste патчи + FAQ-draft + honest forecast |
| Competitive gap | `/app/sites/[siteId]/competitive-gap` | auth | P6 | Разрыв с цитируемыми конкурентами (evidence) |
| Visibility trends | `/app/sites/[siteId]/visibility` | auth | P8 | Тренд с полосой шума («нет ложных побед») + evidence |
| Alert settings | `/app/sites/[siteId]/alerts` | auth | P8 | Каналы email/Telegram/webhook + пороги |
| Approve queue | `/app/sites/[siteId]/approve-queue` | auth (Auto) | P10 | Trust-ladder: pending-очередь + per-type opt-in auto |
| FAQ review | `/app/sites/[siteId]/faq-review` | auth (Auto) | P10 | Staging-предпросмотр FAQ → подтверждение → публикация |
| Audit log + rollback | `/app/sites/[siteId]/audit-log` | auth (Auto) | P10 | Append-only журнал + 1-click rollback |
| DPA acceptance | `/app/sites/[siteId]/dpa` | auth (Auto) | P10 | Акцепт DPA перед первой авто-правкой |
| Prompt-set editor | `/app/sites/[siteId]/prompts` | auth | P9 | Правка авто-сгенерированных probe-промптов (лимит по тарифу) |
| Billing | `/app/billing` | auth | P9 | 3 тарифа × режим Manual/Auto, trial, статус подписки |

---

## Состав каждого экрана

Формат: назначение/блоки → *Состояния* → *PostHog* → *Инварианты в UI*.

### Landing (`/`, P7)
URL-инпут (`Input`+`Button` «Проверить сайт», Zod-валидация URL), краткий оффер (Score + gap + патчи + базовая видимость). Submit → `POST /api/public/audit {url}` → `job_id` → редирект `/audit/[jobId]`.
*Состояния:* `idle`; `submitting`; `error` (невалидный URL inline / 429 → `RateLimitNotice` с `retry_after`).
*PostHog:* `page_viewed`, `tier0_audit_started`.
*Инварианты:* оффер — «аудит и патчи», не «+X% трафика».

### Tier0 result (`/audit/[jobId]`, P7) — async-модель, ДВА ПОРОГА
Результат наполняется поэтапно через polling по `job_id`; страница монтируется сразу с прогрессом и догружает блоки.
- **Порог 1 (≤ 90 сек, «быстрая правда»):** `ScoreGauge` (AI-Readiness Score), `ComponentBreakdown` (Discovery/Comprehension, pass/warn/fail), топ-3 `PatchCard` (copy-paste патчи машиночитаемого слоя). Детерминированный on-site сигнал — точные числа.
- **Порог 2 (≤ 5 мин, «медленная правда»):** догружаются `competitive_gap` (сводка по цитируемым конкурентам) и `visibility_preview` (базовый probe — 1 прогон × 4 модели). До готовности — `Skeleton` + «считаем видимость в ИИ…».
- **Disclaimer (обязателен, AC-4):** `visibility_preview.disclaimer` непустой — «Предварительная оценка (1 прогон, не N≥5); для точных данных с CI — полный мониторинг». Рендер через `ForecastBadge`/`Alert`.
- **Polling:** `GET /api/public/audit/{job_id}` → `{status, score?, components?, patches?, competitors_gap?, visibility_preview?}`; опрос ~2–3 с до `completed`/`failed`; частичный ответ — норма, каждый блок рендерится по появлению своего поля.
- **CTA:** «Зарегистрируйтесь для полного мониторинга» → `/register` (с прокидыванием URL).
*Состояния:* `pending` (оба Skeleton); `partial` (Score готов, видимость грузится); `completed`; `failed` (сообщение + повтор); `expired` (job > TTL 7 дней → новый аудит).
*PostHog:* `tier0_audit_completed`, `score_calculated`, `tier0_cta_clicked`.
*Инварианты:* read-only; disclaimer виден; гарантированного % нет.

### Login / Register (`/login`, `/register`, P9)
Формы входа/регистрации — фактически Keycloak OIDC (Authorization Code + PKCE) + callback-роут. Register стартует trial и (при переходе с Tier0) прокидывает исходный URL в онбординг.
*Состояния:* `idle`; `redirecting`; `error` (OIDC).
*PostHog:* `user_registered`, `trial_started`.
*Инварианты:* JWT безопасно (httpOnly/refresh через backend); `tenant_id` из claims.

### Onboarding wizard (`/app/onboarding`, P9)
Степпер из 4 шагов, цель `time-to-first-verified-fix` < 24 ч: (1) подключение сайта — URL + выбор режима Manual/Auto (для Auto — подсказка про WP-коннектор/DPA, гейт откладывается до первой авто-правки); (2) аудит — запуск + `ScoreGauge`/`ComponentBreakdown`; (3) редактор промптов — предложенный авто-набор (встраивает Prompt-set editor); (4) первая правка — выбор топ-фикса → применение (Auto) или copy-paste (Manual) → показ Readiness-delta (aha).
*Состояния:* пошаговый progress; `loading` на аудите; `error` (сайт недоступен); возврат к шагу.
*PostHog:* `audit_started`, `first_fix_applied`.
*Инварианты:* happy-path без поддержки; DPA-гейт не блокирует вход, только авто-правку.

### Dashboard (`/app`, P6) — первый авторизованный кабинет
Для активного сайта: `ScoreGauge` (текущий Score + delta), `ComponentBreakdown` (раскрытые компоненты Discovery/Comprehension, pass/warn/fail; llms.txt помечен agent-infra, НЕ весит как citation-фактор), счётчики (открытых рекомендаций, применённых правок), переходы к recommendations/visibility.
*Состояния:* `loading` (Skeleton); `empty` (аудит ещё не проходил → CTA «Запустить аудит»); `error`.
*PostHog:* `page_viewed`, `score_calculated`.
*Инварианты:* компоненты Score раскрыты (прозрачность FR-1.3); прогноз видимости — только с диапазоном.

### Recommendations (`/app/sites/[siteId]/recommendations`, P6)
Прио-список `RecommendationRow`, сортировка по `impact_score` DESC; каждая строка: заголовок, `type` (`machine_readable`/`content`), `apply_channel` (`auto`/`review`/`manual-paste`), impact (Readiness-проекция). Разворот → `PatchCard` (JSON-LD snippet / robots.txt строки / llms.txt / FAQ-HTML + инструкция «куда вставить» + copy-to-clipboard). FAQ-фиксы помечены `draft`, ведут в FAQ review. Вверху honest-forecast: `ForecastBadge` — Readiness-проекция (точно) + Visibility (`range_low`–`range_high` + `confidence` + `disclaimer`).
*Состояния:* `loading`; `empty` («сайт в хорошей форме»); `error`.
*PostHog:* `page_viewed`; copy-to-clipboard (custom).
*Инварианты:* `visibility_guarantee` в схеме нет — UI его не рендерит; FAQ всегда `draft` (кнопки «опубликовать» здесь нет); все патчи доступны без API (Manual track).

### Competitive gap (`/app/sites/[siteId]/competitive-gap`, P6)
По каждому целевому промпту: `cited_competitors[]` (url, `schema_types[]`, `has_faq`, `has_answer_first`) рядом с теми же полями сайта клиента, с подсветкой разрыва («у цитируемых есть FAQPage + answer-first, у вас нет»). Только структурные факты — без выдуманных %.
*Состояния:* `loading`; `empty` (нет цитируемых конкурентов → расширить промпты); `error`.
*PostHog:* `page_viewed`.
*Инварианты:* сравнение доказательное, без обещанного %-прироста.

### Visibility trends (`/app/sites/[siteId]/visibility`, P8)
`TrendChart` метрики Visibility/Citation во времени С ПОЛОСОЙ ШУМА (CI-band вокруг линии). Правило «нет ложных побед»: маркер/подпись «значимый рост» ставится ТОЛЬКО при `is_significant=true` (Δ вышел за half-width CI); если Δ внутри полосы — нейтральная подпись «в пределах шума», без заявления победы. Разбивка по 4 моделям (ChatGPT/Perplexity/Алиса-Нейро/GigaChat) и метрикам (Visibility Score, Coverage, Share of Voice, Citation Rate, Stability). Ниже — `EvidenceSnapshot` (скриншоты ответов ИИ до/после, привязка prompt_id/model/date).
*Состояния:* `loading`; `empty` («нужно ≥N прогонов»); `insufficient_data` (широкий CI — флаг недоверия); `error`.
*PostHog:* `page_viewed`.
*Инварианты:* стрелка роста НЕ рисуется внутри CI; сырые распределения — по запросу, не в основном экране; гарантированного % нет.

### Alert settings (`/app/sites/[siteId]/alerts`, P8)
Каналы уведомлений (email / Telegram / webhook — `Switch` + поля адреса/URL/токена) и пороги деградации (насколько за полосу шума метрика должна упасть). Соответствует `notification_configs` (channel, threshold).
*Состояния:* `loading`; сохранённое; `error` (невалидный webhook/токен inline).
*PostHog:* `page_viewed`; сохранение (custom).
*Инварианты:* алерт только при падении ВНЕ полосы шума (no false alert) — объяснено в подписи к порогу.

### Approve queue (`/app/sites/[siteId]/approve-queue`, P10, Auto)
Trust-ladder, две зоны: (1) очередь `pending`-правок (`ApproveQueueItem`: тип, target_url, diff-предпросмотр, «Применить»/«Отклонить»); (2) per-type opt-in — `Switch` на каждый ТИП машиночитаемой правки (JSON-LD / robots.txt / llms.txt / IndexNow). FAQ/видимый контент в переключателе физически отсутствует — только ссылка на FAQ review.
*Состояния:* `loading`; `empty`; `dpa_required` (`DpaGate` перекрывает действия); `connector_not_configured` (нет WP-коннектора → Manual/подключить); `error`.
*PostHog:* `fix_applied`.
*Инварианты:* FAQ/видимый контент НИКОГДА не в auto-toggle (§6.10 charter); apply недоступен без DPA и без коннектора.

### FAQ review (`/app/sites/[siteId]/faq-review`, P10, Auto)
FAQ-драфты (answer-first, 50–150 слов, статус `draft`): staging-предпросмотр (как будет на сайте) → явное подтверждение → публикация. Авто-публикация физически заблокирована: кнопки «авто» нет, только «Опубликовать после проверки».
*Состояния:* `loading`; `empty`; `published`; `error`.
*PostHog:* `page_viewed`; публикация FAQ (custom).
*Инварианты:* публикация только после явного подтверждения (обход → backend 422); пути авто-публикации в UI нет.

### Audit log + rollback (`/app/sites/[siteId]/audit-log`, P10, Auto)
Append-only журнал правок и откатов: `fix_id`, `type`, `target_url`, `diff`, `initiated_by`, `applied_at`, `status`, `action` (apply/rollback). У применённых — `Button` «Откатить» → `POST /autofix/{id}/rollback` + `Dialog` подтверждения.
*Состояния:* `loading`; `empty`; `error`; после rollback — новая строка `action: rollback` (журнал только дополняется).
*PostHog:* `page_viewed`; rollback (custom).
*Инварианты:* журнал read-only в UI (нет edit/delete — append-only); rollback сам логируется.

### DPA acceptance (`/app/sites/[siteId]/dpa`, P10, Auto)
Версионированный текст Data Processing Agreement (`ScrollArea`) + акцепт (`Checkbox` «прочитал и согласен» + `Button` «Подписать»). Хранит `tenant_id`, `signed_at`, `version`, `hash`. Гейт: до акцепта auto-fix недоступен (Auto-действия перекрыты `DpaGate`).
*Состояния:* `not_signed` (гейт активен); `signed` (дата/версия, read-only); `error`.
*PostHog:* `page_viewed`; DPA signed (custom, trust-метрика).
*Инварианты:* акцепт неизменяем; auto-fix недоступен до подписи (backend 403 `dpa_required`).

### Prompt-set editor (`/app/sites/[siteId]/prompts`, P9)
Авто-сгенерированный набор probe-промптов (из сущностей/тем сайта), редактируемый: добавить/изменить/удалить. Счётчик лимита по тарифу (breadth-gate). Набор версионируется.
*Состояния:* `loading`; сохранённое; `limit_reached` (лимит промптов тарифа → подсказка апгрейда); `error`.
*PostHog:* `page_viewed`; изменение набора (custom).
*Инварианты:* лимит gated по entitlements; версионирование сохраняется.

### Billing (`/app/billing`, P9)
3 тарифа (Starter 5 990 ₽ / Pro 14 990 ₽ / Business 29 990 ₽) карточками с breadth-различиями (сайты, частота probe, глубина правок, CMS-коннекторы). Переключатель режима **Manual / Auto** (Auto = авто-применение + rollback, требует API+DPA). Статус подписки/trial (`trial_ends_at`, `paid_until`), оплата через ЮKassa (физ/юр).
*Состояния:* `trial`; `active`; `suspended` (неоплата → продлить); `loading`; `error`; `plan_limit_exceeded` (`RateLimitNotice`).
*PostHog:* `page_viewed`; `converted_to_paid` (после webhook-подтверждения).
*Инварианты:* тарифы гейтят breadth, не moat (auto-fix есть и в Starter Auto); Manual не показывает auto-функции доступными.

---

## Навигация

**Публичный флоу:** `/` (landing) → `/audit/[jobId]` (Tier0, async) → CTA → `/register` → `/app/onboarding` → `/app`.

**Сайдбар кабинета** (`/app/...`, скоуп активного сайта через селектор вверху):
- Обзор → `/app`
- Рекомендации → `/app/sites/[siteId]/recommendations`
- Конкуренты → `/app/sites/[siteId]/competitive-gap`
- Видимость → `/app/sites/[siteId]/visibility`
- Промпты → `/app/sites/[siteId]/prompts`
- Алерты → `/app/sites/[siteId]/alerts`
- **Авто-правки** (группа, видима только в Auto-режиме): Очередь → `.../approve-queue`; FAQ на проверку → `.../faq-review`; Журнал изменений → `.../audit-log`; DPA → `.../dpa`
- Внизу: селектор сайта, Тариф/Биллинг → `/app/billing`, профиль/выход.

Группа «Авто-правки» скрыта/задизейблена для Manual-тенантов (entitlements `mode=manual`); попытка доступа → редирект на billing с подсказкой апгрейда.

---

## Компонентная база (переиспользуемые)

| Компонент | Назначение | Ключевые пропсы |
|---|---|---|
| `ScoreGauge` | Индикатор AI-Readiness Score | `score`, `delta?` |
| `ComponentBreakdown` | Компоненты Score (pass/warn/fail; llms.txt = agent-infra) | `components[]` |
| `PatchCard` | Copy-paste патч + инструкция + copy-to-clipboard | `artifactType`, `content`, `instruction` |
| `RecommendationRow` | Строка прио-списка: тип, канал, impact, разворот в PatchCard | `fix`, `impactScore` |
| `TrendChart` | Тренд Visibility с CI-band + маркер значимости | `series[]`, `ciBand`, `isSignificant` |
| `ForecastBadge` | Honest-forecast: диапазон + confidence + disclaimer (НИКОГДА не single-%) | `rangeLow`, `rangeHigh`, `confidence`, `disclaimer` |
| `ApproveQueueItem` | Pending-правка trust-ladder: тип, diff, approve/reject | `fix`, `onApprove`, `onReject` |
| `DpaGate` | Оверлей, перекрывающий Auto-действия без подписанного DPA | `signed`, `dpaUrl` |
| `RateLimitNotice` | Лимит (429 Tier0 / plan_limit_exceeded) + retry/апгрейд | `kind`, `retryAfter?` |
| `EvidenceSnapshot` | Скриншот ответа ИИ до/после + привязка prompt/model/date | `imagePath`, `promptId`, `model`, `capturedAt` |

Дополнительно из shadcn/ui напрямую: `Card`, `Table`, `Tabs`, `Dialog`, `Badge`, `Switch`, `Progress`, `Skeleton`, `Toast`, `Alert`, `Form`.

---

## Соответствие фазам

| Фаза | Экраны, отгружаемые в этой фазе |
|---|---|
| **P6** | Dashboard (`/app`), Recommendations, Competitive gap — первый авторизованный кабинет (read-only). Компоненты: `ScoreGauge`, `ComponentBreakdown`, `RecommendationRow`, `PatchCard`, `ForecastBadge`. |
| **P6.5** | Нет самостоятельных экранов. Probe/metrics-инкремент (P5→UI) встраивается виджетами видимости в Dashboard/Recommendations; отдельная страница трендов — в P8. |
| **P7** | Landing (`/`), Tier0 result (`/audit/[jobId]`) — публичный async-флоу (два порога + disclaimer). PostHog `tier0_*` воронка. |
| **P8** | Visibility trends (`TrendChart` с CI-band, «нет ложных побед»), Alert settings, встраивание `EvidenceSnapshot`. |
| **P9** | Login, Register (Keycloak OIDC), Onboarding wizard (4 шага), Billing (3 тарифа × Manual/Auto), Prompt-set editor. Каркас сайдбара + entitlements-гейтинг навигации. |
| **P10** | Approve queue (trust-ladder), FAQ review, Audit log + rollback, DPA acceptance. Компоненты `ApproveQueueItem`, `DpaGate`. Группа «Авто-правки» в сайдбаре. |

---

*UI-SPEC v1.0 · 2026-07-07 · инвентарь экранов MVP; детали компонентов — JIT при планировании фазы frontend-implementer'ом.*
