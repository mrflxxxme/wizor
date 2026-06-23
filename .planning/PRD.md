---
title: "PRD — AI Visibility / AI Readiness Platform (РФ)"
type: PRD
status: draft v0.2
owner: Product
created: 2026-06-23
source_doc: "AI Visibility SaaS RF 2026 (v2.0, 2026-05-08)"
horizon: "24 месяца, фазы A→B→C (rolling-wave)"
review_cadence: "каждые 4 недели (категория ранней зрелости)"
---

# PRD — AI Visibility / AI Readiness Platform для РФ

> **Назначение документа.** Это product requirements для поэтапного (итерационного) создания продукта. На его основе пишется ТЗ. Фаза 1 (MVP) специфицирована детально (функциональные требования + критерии приёмки), фазы B и C — рамочно (цели, scope, exit-gates) и уточняются по мере прохождения gate'ов (rolling-wave planning).
>
> **Происхождение.** Документ собран на основе «AI Visibility SaaS RF 2026» (оценка рыночной возможности, 2026-05-08) + интервью с продакт-аналитиком + верификация против актуального рынка (июнь 2026). Все стратегические развилки верифицированы заказчиком.

---

## 0. Резюме принятых решений (decision log)

| # | Решение | Выбор |
|---|---------|-------|
| 1 | Горизонт PRD | Многослойный A→B→C, 24 мес; MVP детально, B/C рамочно |
| 2 | Входной клин | **A-first, но дифференцированный**: SMB self-serve + тонкий срез auto-fix + multi-tenant-ready |
| 3 | Порядок CMS-коннекторов | **WordPress → Tilda → Bitrix → Modx/OpenCart** |
| 4 | Auto-fix (авто-применение) в MVP | Только **невидимый машиночитаемый слой** (robots / llms.txt / JSON-LD / IndexNow) |
| 5 | Модель контроля auto-fix | **Approval-gate → opt-in auto**; audit log + rollback + DPA обязательны в MVP |
| 6 | Модели в MVP | **ChatGPT + Perplexity + Алиса/Нейро + GigaChat**; dual-geo probe с дня 1; DeepSeek/Claude → A.4 |
| 7 | Набор probe-промптов | **Гибрид**: авто-генерация + курирование пользователем |
| 8 | Метрики | **Uncertainty-aware внутри, упрощённый UI снаружи**; sentiment → фаза B |
| 9 | Верификация | **Двухуровневая**: Readiness-delta (быстро) + Visibility/Citation-delta (медленно) + evidence; A/B → C |
| 10 | North Star | **Verified AI-Readiness uplift**; активация — time-to-first-verified-fix |
| 11 | Триггеры фаз | **Evidence-gates + pivot-дедлайны** |
| 12 | Упаковка/pricing | **Auto-fix во всех тарифах, гейтим breadth**; full-feature trial |
| 13 | LLM-стратегия | **Provider-agnostic router, RU-default + OSS self-hosted**, иностранные opt-in |
| 14 | GTM MVP | **Кейсы + контент/комьюнити → потом performance** |
| 15 | Discovery | **Phase 0 (нед. 0–8) параллельно с базовой инфрой, gate на тяжёлый auto-fix**; domain-expertise constraint |
| 16 | Рыночные корректировки | llms.txt репозиционирован; FAQ-драфт+review добавлен в MVP; retrieval-first; trial ≥ 21–30 дн |
| 17 | Доступ и воронка | **Tier 0 Instant Audit (no-auth) + Manual track (без API) + Auto track (API+DPA)**; forecast honest; предиктивная модель — roadmap (см. §4.1) |

---

## 1. Видение и стратегическое позиционирование

**Видение.** Сделать любой сайт **комплексно доступным для ИИ** — для retrieval-пайплайнов LLM, для AI-агентов и для embedding-сервисов — и довести это до измеримого результата автоматически, замыкая полный цикл: **Аудит → Мониторинг → Рекомендации → Авто-имплементация → Верификация.**

**Категория.** Не «GEO-инструмент», а **AI Readiness Platform**. Это шире, защитимее и обосновывает enterprise-цены.

**Главный дифференциатор (moat).** Автоматическая имплементация изменений на стороне сайта — этого не делает ни один игрок РФ-рынка (все заканчиваются на «вот рекомендация → внедрите сами»). Второй слой защиты — **покрытие RU-стека** (Алиса/Нейро, GigaChat), с которым не работает ни один глобальный сервис (Profound, Otterly, ZipTie и др.).

**Стратегический принцип (из источника, подтверждён рынком).** Дифференциация достигается **не выбором технологий, а интеграционным слоем** (CMS-коннекторы, MCP-сервер, embedding-pipeline). Сюда вкладываются инженерные усилия.

---

## 2. Проблема и рыночная возможность

### 2.1. Боль пользователя
Главный незакрытый разрыв рынка — **insights-to-action**: «вижу данные в дашборде, но не знаю, что чинить, и тем более не могу это внедрить». Это глобальная, а не только российская проблема (подтверждено ZipTie).

### 2.2. Рынок (верифицировано, июнь 2026)
- **Глобально категория состоялась и хорошо профинансирована.** Profound: **$96M Series C при оценке $1 млрд** (фев. 2026), 700+ enterprise-клиентов, ~10% Fortune 500; 20–30% SEO-бюджетов мигрируют в AI-поиск.
- **РФ:** ~30–35 млн ежемесячных пользователей LLM; ~25% поисковых запросов с участием ИИ; 40%+ используют нейросети как первичный канал поиска товаров/услуг.
- **Распределение AI-рефералов на РФ-сайты** (источник: ADPASS/Digital Budget, янв–окт 2025): ChatGPT 54,1%; Perplexity 32,8%; DeepSeek 8,2%; Алиса 3,3%; GigaChat 1,6%.
- **Конверсия AI-трафика** в разы выше органики (множители 4–14×+ по разным источникам — относиться как к ориентиру, не как к гарантии; см. §16 «риск метрик»).

### 2.3. Конкуренты РФ
Мониторинг-платформы: VisioBrand, Шпиониро (white-label, от 1 490 ₽), AI Пиксель Тулс, GPTFox, mePulse. GEO-агентства: NeuroReach, Kokoc, Пиксель Плюс, Red Orange, Ашманов и др. **Все покрывают 2 из 3 этапов** (мониторинг + рекомендации); имплементация — руками клиента/агентства.

### 2.4. Окно возможности
**12–18 месяцев** до агрессивных запусков от крупных холдингов (Kokoc, Пиксель, Ашманов) и потенциальных нативных решений Яндекс/Сбер. **Уточнение по рынку: окно скорее сужается** — глобальные плейбуки зреют быстро и капитализированы. Скорость вывода MVP — критическое условие успеха.

---

## 3. Продуктовые принципы (доктрины)

Эти принципы пронизывают все требования и обязательны к соблюдению в проектировании и ТЗ.

1. **Differentiation lives in the integration layer.** Инженерный фокус — на коннекторах и авто-имплементации, не на «ещё одном дашборде».
2. **Honest uncertainty.** LLM-метрики недетерминированы. Никогда не показываем одно «детерминированное» число — всегда с полосой шума (N≥5 прогонов + доверительный интервал). «Реальное» изменение = выход за полосу шума.
3. **Two-tier proof.** Разделяем быстрый детерминированный **Readiness-сигнал** (on-site, мгновенно) и медленный вероятностный **Visibility-сигнал** (выдача ИИ, дни-недели). Первый — онбординг-хук, второй — retention-доказательство.
4. **Trust ladder.** Авто-правки на чужой production: approval-gate по умолчанию → opt-in авто-применение по типу правки. Всегда audit log + 1-click rollback + подписанный DPA.
5. **Retrieval-first.** Оптимизируем и измеряем на **retrieval/RAG-поверхностях** (Perplexity, ChatGPT Search, Яндекс Нейро/Алиса, Gemini AIO), где правки реально распространяются; «память» модели не таргетируем.
6. **Compliance by design.** 152-ФЗ заложен в архитектуру; on-premise опция; данные клиента по умолчанию обрабатываются RU-моделями.
7. **Evidence-gated scaling.** Каждая фаза валидирует свою рисковую гипотезу до финансирования следующей.
8. **Read-only first.** Аудит, готовые патчи, базовая Visibility и верификация *применённого* (через re-crawl) работают по одной ссылке, без доступа к сайту. Запись/API нужны только для авто-применения. Продукт входит без трения (no-auth), а API/DPA — это апгрейд, а не порог входа (см. §4.1).

---

## 4. Клиентские сегменты, ICP и JTBD

| | Сценарий A (MVP) | Сценарий B | Сценарий C |
|---|---|---|---|
| **Сегмент** | SMB self-serve | Agency white-label | Enterprise full-cycle |
| **ICP** | Владельцы малого бизнеса, фрилансеры-маркетологи, owner-операторы small e-com | SEO/SERM-агентства (~500 в РФ) + freelance-консультанты | Топ-300 e-com и крупный B2B (Wildberries/Ozon-партнёры, M.Видео, корп. сайты) |
| **Модель** | Self-serve, low-touch | Multi-tenant, agency-led | High-touch, dedicated CSM, on-prem опция |
| **ARPU (ориентир)** | 8 000–12 000 ₽/мес | 80 000–150 000 ₽/мес | 400 000–700 000 ₽/мес |
| **Глубина AI-readiness** | Discovery + Comprehension | + базовая Integration | Все 3 уровня + MCP + embeddings |

**JTBD (Сценарий A, основной для MVP):**
- *«Когда клиенты всё чаще ищут товары/услуги через нейросети, я хочу, чтобы мой сайт попадал в их ответы — но я не SEO-эксперт и у меня нет агентского бюджета, поэтому мне нужно, чтобы система сама нашла проблемы и сама их починила, а я лишь подтвердил.»*
- *«Я хочу видеть доказательство, что это работает, прежде чем платить дальше.»*

### 4.1. Модель доступа и воронка: Tier 0 / Manual / Auto (read-only first)

**Ключевая развязка архитектуры доступа.** Аудит, готовые патчи, замер текущей видимости и даже верификация *применённого* работают **по одной ссылке (read-only)**. Доступ на запись (CMS API/plugin) нужен ровно для одного — **автоматически внести** правку. Это даёт три дорожки и снимает трение на входе.

| Дорожка | Доступ | Что входит | Роль |
|---|---|---|---|
| **Tier 0 — Instant Audit** | URL, no-auth | AI-Readiness Score + competitive gap + готовые copy-paste патчи + базовая Visibility (probe) | Бесплатный PLG-вход, лид-магнит, материал для кейсов |
| **Manual track** | без API (read-only) | + регулярный мониторинг, прио-рекомендации, патчи копипастом, **re-crawl верификация** применённого | Платный для тех, кто не даёт write-доступ |
| **Auto track** | API + DPA | + авто-применение машиночитаемого слоя, FAQ через review, rollback, closed-loop attribution → данные для предиктивной модели | Премиум-апгрейд: moat + data-flywheel |

**Что можно/нельзя без API:** *можно* — краулинг и аудит, генерация патчей (JSON-LD, robots, llms.txt, FAQ-драфты), probe-видимость, проверка повторным краулом, что правка появилась в HTML. *Нельзя* — автоматически записать правку и сделать rollback (только Auto track).

**Честность прогноза (доктрина honest uncertainty) — три уровня:**
1. **Readiness-проекция** (детерминированно, без API): «примените эти фиксы → Score X→Y; вот какие дают больше всего». ✅ Можно сразу.
2. **Competitive gap** (доказательно): краулим конкурентов, которых *сейчас цитируют* по целевым промптам, и показываем разрыв («у цитируемых есть FAQPage-schema + answer-first блоки, у вас нет»). ✅ Не выдуманный процент — evidence.
3. **Visibility-% прогноз**: только как **диапазон с доверием + индустриальные бенчмарки**, не гарантия. Точная site-specific предиктивная модель — **roadmap-айтем**, обучается на before/after данных Auto track. ⚠️ Никаких обещанных «+30%».

> **Стратегический эффект:** это де-рискит гипотезу №1 (готовность дать API) — продукт монетизируется и без write-доступа (Manual track), а auto-apply становится апгрейдом, а не порогом входа. **DPA/API — gate только Auto track, а не входа в продукт.**

---

## 5. North Star и дерево метрик

**North Star: Verified AI-Readiness Uplift** — число сайтов, на которых применён ≥1 auto-fix **и** зафиксирована положительная Readiness-delta (вне полосы шума).

- **Активационная под-метрика:** `time-to-first-verified-fix` — медиана времени от регистрации до первой применённой правки с ростом Readiness. Цель MVP: < 24 часов (self-serve), < 72 часов с учётом review-правок.
- **Guardrail (долгосрочный, запаздывающий):** Visibility/Citation uplift на retrieval-поверхностях.
- **Бизнес-выходы:** MRR, число платящих сайтов, M3-retention, LTV/CAC.

```
North Star: Verified AI-Readiness Uplift
├── Activation: time-to-first-verified-fix, % сайтов с applied fix
├── Value (guardrail): Visibility/Citation delta (retrieval surfaces)
├── Trust: % auto-apply opt-in, rollback-rate, DPA-sign rate
└── Business: MRR, paying sites, M3-retention, LTV/CAC (≥3)
```

---

## 6. Полный цикл AI-readiness (продуктовая модель)

| Этап | Что делает | Покрытие конкурентами | Глубина в MVP |
|---|---|---|---|
| 1. Аудит | Скан сайта: robots, schema, llms.txt, CWV, FAQ, индексируемость | ✓ есть у всех | Паритет |
| 2. Мониторинг | Probe в LLM, share of voice, citation tracking | ✓ есть у всех | Паритет (uncertainty-aware) |
| 3. Рекомендации | Что чинить, приоритизация, прогноз impact | ◐ частично | Паритет+ (приоритизация по impact) |
| 4. **Имплементация** | **Авто-внесение изменений (schema, robots, llms.txt, IndexNow; FAQ через review)** | ✗ **никто** | **Дифференциатор (тонкий срез)** |
| 5. Верификация | Замер эффекта, evidence, алерты деградации | ◐ базово | Двухуровневая |

---

## 7. Три уровня доступности сайта для ИИ (с рыночной корректировкой)

### 7.1. Discovery layer — как ИИ находит сайт
robots.txt (явные разрешения AI-ботам по типам: training vs real-time fetch), XML sitemap, IndexNow (быстрое уведомление Bing/Я.Вебмастер — критично: на Bing-индексе стоят и ChatGPT Search, и Perplexity), Core Web Vitals, доступность контента без client-side рендеринга, корректные коды ответов.

> 🔴 **Корректировка: `llms.txt` НЕ относится к Discovery с точки зрения цитируемости.** Подтверждено рынком (июнь 2026): AI-поисковые краулеры его практически не читают (408 обращений из 500M визитов AI-ботов); Google официально не поддерживает; удаление переменной llms.txt из citation-моделей их улучшало. **llms.txt переносится в Integration layer** (его читают агенты/IDE/MCP). В продукте он генерируется (дёшево, future-proof для агентов), но **не позиционируется как citation-драйвер и не весит в AI-Readiness Score как фактор видимости.**

### 7.2. Comprehension layer — как ИИ понимает контент **(основной citation-левер)**
- Schema.org через JSON-LD: Organization, WebSite, Article/BlogPosting, Person, Product, FAQPage, HowTo, LocalBusiness, Speakable. *(Подтверждено: ×2.5 шанс попасть в AI-ответ; Bing подтвердил, что schema помогает LLM понимать контент.)*
- Entity-граф через `@id` — связывание сущностей в knowledge graph сайта.
- Семантическая HTML-структура (h1→h2→h3, article/section/nav/aside).
- **FAQ-блоки и answer-first чанкинг (50–150 слов)** — *первичный* citation-левер (schema+FAQ: +44% цитирований, BrightEdge).
- Свежесть/recency-сигналы (важны для retrieval-поверхностей).

### 7.3. Integration layer — как ИИ активно использует сайт (Сценарий C)
MCP-сервер сайта, public content API (REST/GraphQL, очищенный Markdown/JSON для RAG), vector embeddings as a service, agent-friendly forms (ARIA, семантика — для browser-агентов), product feeds (Я.Маркет, Wildberries/Ozon, Google Shopping), webhook content sync, LLM-export endpoints (`/llm-context.md`, `/llm-knowledge.json`), **llms.txt/llms-full.txt** (его реальный дом).

> 🟢 **Подтверждено:** спрос на MCP реален (97M загрузок SDK/мес, 10k+ публичных серверов, 41% компаний в проде). Но «MCP-сервер на маркетинговый сайт» как конкретный спрос — **гипотеза**, валидируется в дискавери фазы C.

---

## 8. Фазовый роадмап и exit-gates

**Модель переходов: evidence-gates + pivot-дедлайны.** Переход в следующую фазу — только при выполнении gate-критериев; календарные чекпоинты форсируют явное решение go / pivot / stop.

```
Phase 0  Discovery & De-risking      нед. 0–8 (параллельно с базовой инфрой)
   └─ gate: 5 гипотез подтверждены → старт тяжёлого auto-fix
Phase A  MVP / SMB self-serve         мес. 1–12
   └─ A→B gate (evidence) + pivot-дедлайн (мес. 9)
Phase B  Agency white-label           мес. 6–18 (внахлёст, на базе A)
   └─ B→C gate (evidence) + pivot-дедлайн
Phase C  Enterprise + Integration     мес. 12–24+
```

### A→B gate (все условия)
1. ≥ N сайтов с **verified Readiness-uplift** и наблюдаемым Visibility-сдвигом на ≥1 retrieval-поверхности.
2. **Готовность давать API-доступ / подписывать DPA доказана** (риск №1 тезиса) — на реальной выборке.
3. Надёжность auto-fix: rollback-rate ниже порога, ноль инцидентов порчи production.
4. Пол MRR + здоровый сигнал retention (напр., M3-retention ≥ целевого).
5. Входящий интерес ≥ 3–5 агентств.
- **Pivot-дедлайн (мес. 9):** если gate не достигнут — явное решение pivot (в чистый agency-tool / сужение ICP) или stop.

### B→C gate (все условия)
1. Adoption агентств доказан (N агентств, NRR > порога).
2. Enterprise-pull: подписанные LOI/пилоты.
3. Спрос на Integration layer (MCP/embeddings) валидирован на конкретных клиентах.

---

## 9. ФАЗА 1 — MVP / Сценарий A (детальная спецификация)

### 9.0. Phase 0 — Discovery & De-risking (нед. 0–8, параллельно)
**Цель:** снять 5 рисковых гипотез до тяжёлой разработки auto-fix. **Метод:** 30 customer-development интервью (15 SMB-владельцев + 5 фрилансеров + 10 owner-операторов small e-com) + технические спайки.

**Гипотезы-гейты (go/no-go для CMS-коннекторов):**
- H1. Клиенты готовы дать API-доступ к сайту для авто-правок.
- H2. Есть готовность платить за авто-имплементацию (vs ручная работа).
- H3. Агентства готовы рассмотреть переход со Шпиониро/VisioBrand ради auto-fix.
- H4. Реальный time-to-citation RU/retrieval-поверхностей на новый контент (замер спайком).
- H5. Юр-готовность подписать DPA на авто-правки.

**Параллельно строится** базовая инфра, нужная при любом исходе (краулер, probe, скоринг). **Тяжёлые CMS-коннекторы стартуют только после прохождения gate.**

### 9.1. Scope MVP

**В scope (In):**
- **Tier 0 «Instant Audit» (no-auth):** ссылка → AI-Readiness Score + competitive gap + готовые copy-paste патчи + базовая Visibility. PLG-вход (см. §4.1).
- **Two-track модель доступа:** Manual track (без API — патчи копипастом + re-crawl верификация) и Auto track (API+DPA — авто-применение + rollback).
- Аудит сайта (Discovery + Comprehension).
- Probe-мониторинг 4 моделей (ChatGPT, Perplexity, Алиса/Нейро, GigaChat), dual-geo.
- AI-Readiness Score + Visibility-метрики (uncertainty-aware).
- Рекомендации с приоритизацией по impact.
- **Auto-fix (авто-применение): машиночитаемый слой** — robots.txt, JSON-LD schema, IndexNow, llms.txt (как agent-infra).
- **FAQ-генерация (answer-first) с обязательным review-применением** (видимый контент → не авто).
- Approval-gate → opt-in auto; audit log; 1-click rollback/версионирование; DPA-флоу.
- CMS-коннектор: **WordPress** (полный write-доступ).
- Двухуровневая верификация + evidence-захват (скриншоты ответов ИИ).
- Биллинг (ЮKassa), аутентификация (Keycloak), self-serve онбординг, 3 тарифа, trial.
- Multi-tenant-ready архитектура (без полного agency-UX).

**Вне scope (Out, → последующие фазы/этапы):**
- Tilda/Bitrix коннекторы (A.4), Modx/OpenCart/Shopify (B/C).
- Auto-применение видимого контента (FAQ авто-публикация, answer-first переписывание абзацев).
- Sentiment-трекинг, competitive benchmarking, PDF/PPTX-отчёты (фаза B).
- White-label кабинет, agency-billing, bulk-операции (фаза B).
- MCP-сервер, content API, embeddings, product feeds, agent-forms, A/B-тест (фаза C).
- DeepSeek/Claude в probe (A.4).

### 9.2. Эпики и функциональные требования (с критериями приёмки)

> Формат: `FR-x` — требование; **AC** — критерии приёмки (минимум для «готово»).

#### EPIC 1 — Аудит сайта
- **FR-1.1** Краулер сканирует сайт (Crawlee + Playwright для SPA): robots.txt, sitemap, HTTP-коды, структура HTML (h1–h3, semantic tags), наличие JSON-LD, наличие FAQ-блоков, Core Web Vitals, индексируемость (Bing/Я.Вебмастер).
  - **AC:** для сайта до N страниц аудит завершается < T мин; формируется структурированный отчёт по каждому пункту с пометкой pass/warn/fail; обрабатываются SPA (контент после рендера).
- **FR-1.2** Schema-валидатор (rdflib + custom JSON-LD validator) проверяет корректность разметки до публикации.
  - **AC:** невалидный JSON-LD не публикуется; пользователь видит причину.
- **FR-1.3** Расчёт **AI-Readiness Score** (детерминированный, on-site) по взвешенным факторам Discovery+Comprehension.
  - **AC:** Score воспроизводим (одинаковый вход → одинаковый выход); **llms.txt НЕ входит в citation-вес**; компоненты Score раскрыты пользователю.

#### EPIC 2 — Probe-мониторинг
- **FR-2.1** Гибридный набор промптов: система генерит 20–30 кандидатов из сущностей/тем сайта; пользователь правит/добавляет/удаляет.
  - **AC:** при онбординге пользователь получает готовый предложенный набор за < T; может отредактировать; набор версионируется.
- **FR-2.2** Probe выполняется по 4 моделям dual-geo: Алиса/Нейро + GigaChat — через RU API (Yandex Cloud Foundation Models / GigaChat API); ChatGPT/Perplexity — через зарубежные ноды (Hetzner/Selectel) + резидентные прокси; web-scraping fallback там, где нет API.
  - **AC:** ни один probe к ChatGPT/Perplexity не идёт с РФ-IP; настроены retry/ротация прокси (httpx + tenacity); сбои логируются и не «роняют» весь батч.
- **FR-2.3** Каждый промпт прогоняется **N ≥ 5 раз** на модель; результаты агрегируются с доверительным интервалом / полосой стабильности.
  - **AC:** для каждой метрики хранится распределение по прогонам и CI.
- **FR-2.4** Метрики: **Visibility Score** (композит) + **Coverage/Presence**, **Share of Voice**, **Citation Rate** (сайт процитирован/дан ссылкой как источник, отдельно от упоминания), **Stability**.
  - **AC:** UI показывает Score + 4 компонента с полосой шума; сырые распределения доступны по запросу (не в основном экране).

#### EPIC 3 — Рекомендации
- **FR-3.1** Генерация прио-листа фиксов с прогнозом impact и пометкой «авто-применимо / требует review».
  - **AC:** топ-фиксы отсортированы по ожидаемому impact; для каждого указан тип (машиночитаемый/контент) и канал применения.
- **FR-3.2** FAQ-генератор (answer-first, 50–150 слов) через LLM-router (RU-default).
  - **AC:** сгенерированный FAQ помечается как **draft**; не публикуется без review.
- **FR-3.3** **Competitive gap analysis:** краул конкурентов, которых цитируют LLM по целевым промптам; сравнение их Readiness/структуры с сайтом клиента; вывод разрыва как доказательной базы прогноза.
  - **AC:** для каждого целевого промпта показаны цитируемые источники и конкретные структурные отличия (schema-типы, FAQ, answer-first); без выдуманных процентов.
- **FR-3.4** **Готовые патчи (copy-paste) для Manual track:** каждая рекомендация сопровождается применимым артефактом (JSON-LD-сниппет, строки robots.txt, контент llms.txt, FAQ-блок) с инструкцией «куда вставить».
  - **AC:** артефакт валиден и самодостаточен; доступен без подключения API.
- **FR-3.5** **Прогноз эффективности (honest):** Readiness-проекция (детерминированно) + competitive gap; Visibility-прогноз — только диапазон с доверием/бенчмарками, помеченный как оценка.
  - **AC:** UI нигде не показывает гарантированный Visibility-%; все вероятностные прогнозы помечены и сопровождаются доверительным диапазоном.

#### EPIC 4 — Имплементация (auto-fix) — ДИФФЕРЕНЦИАТОР
- **FR-4.1** WordPress-коннектор (custom plugin → WP REST API) авто-применяет: запись JSON-LD в `<head>`, robots.txt (разрешения AI-ботам), генерацию/публикацию llms.txt/llms-full.txt, IndexNow-пинг.
  - **AC:** правки применяются на реальном WP-сайте; каждая правка обратима; повторное применение идемпотентно.
- **FR-4.2** **Trust ladder:** по умолчанию каждое изменение в очередь на approve; пользователь может включить `auto-apply` по конкретному типу машиночитаемой правки.
  - **AC:** видимый контент (FAQ) **никогда** не авто-применяется; только машиночитаемый слой может быть переведён в auto.
- **FR-4.3** FAQ-блоки публикуются только через **review/merge-flow** (предпросмотр → подтверждение → публикация).
  - **AC:** есть staging-предпросмотр; публикация только после явного подтверждения.
- **FR-4.4** **Audit log** всех авто-изменений (что, где, когда, кем инициировано, diff).
  - **AC:** каждая правка фиксируется с diff и timestamp; журнал неизменяем (append-only).
- **FR-4.5** **Версионирование + 1-click rollback** к предыдущему состоянию.
  - **AC:** любую применённую правку можно откатить одним действием; откат тоже логируется.
- **FR-4.6** **DPA-флоу:** до первой авто-правки клиент подписывает соглашение о разрешении автоматических изменений.
  - **AC:** auto-fix недоступен до акцепта DPA; факт акцепта хранится.
- **FR-4.7** **Manual track (без API):** для сайтов без подключённого коннектора система отдаёт готовые патчи копипастом; авто-применение и rollback недоступны, но доступна re-crawl верификация (FR-5.5).
  - **AC:** весь путь аудит→рекомендации→патчи работает без write-доступа; **DPA/API требуются только для Auto track**, а не для входа в продукт.

#### EPIC 5 — Верификация
- **FR-5.1** **Readiness-delta** (быстро): пересчёт AI-Readiness Score до/после правки, мгновенно и детерминированно.
  - **AC:** после применения правки пользователь сразу видит прирост Score с указанием, какая правка его дала.
- **FR-5.2** **Visibility/Citation-delta** (медленно): повторные probe во времени на retrieval-поверхностях; «реальный» сдвиг = выход за полосу шума.
  - **AC:** тренд показывается с полосой шума; система не заявляет улучшение внутри шума.
- **FR-5.3** **Evidence-захват:** скриншоты/снапшоты ответов ИИ до/после (для кейсов и доверия).
  - **AC:** снапшоты сохраняются с датой и привязкой к промпту/модели.
- **FR-5.4** Алерты деградации (падение видимости) — email/Telegram/webhook.
  - **AC:** при падении метрики вне полосы шума отправляется алерт.
- **FR-5.5** **Re-crawl верификация (работает в Manual track):** повторный краул публичных страниц подтверждает, что правка появилась в HTML (schema/FAQ/robots/llms.txt), даже если применена вручную.
  - **AC:** система детектирует факт применения без API; Readiness-delta пересчитывается по фактическому состоянию HTML.

#### EPIC 6 — Платформа / биллинг / онбординг
- **FR-6.1** Self-serve онбординг: подключение сайта → аудит → предложенные промпты → первая правка (aha).
  - **AC:** `time-to-first-verified-fix` для типового WP-сайта < 24 ч; целевой happy-path без участия поддержки.
- **FR-6.2** Аутентификация (Keycloak/OIDC), multi-tenant-ready модель данных (tenant_id с дня 1).
  - **AC:** схема данных изолирует тенантов; переход в agency-режим (фаза B) не требует миграции архитектуры.
- **FR-6.3** Биллинг (ЮKassa: физ + юр лица), 3 тарифа, full-feature trial.
  - **AC:** тарифы гейтят breadth (см. §9.4); trial конвертируется в платный без потери данных.

### 9.3. Нефункциональные требования и архитектурные constraints (для ТЗ)
- **NFR-1 (152-ФЗ).** Хостинг и обработка ПД клиентов — в РФ (Yandex Cloud). Уведомление в Роскомнадзор; политика обработки ПД; DPA с клиентами.
- **NFR-2 (dual-geo).** Probe-инфра разнесена: RU-ноды (RU-модели) + зарубежные ноды + резидентные прокси (ChatGPT/Perplexity). **С дня 1.**
- **NFR-3 (LLM-router).** Provider-agnostic абстракция; content-gen по умолчанию RU (GigaChat/YandexGPT); OSS self-hosted (Qwen 2.5 / Saiga via vLLM) для batch-cost; иностранные модели — opt-in для не-чувствительных задач. Минимизировать vendor lock-in (LangChain/LlamaIndex — минимально).
- **NFR-4 (надёжность auto-fix).** Идемпотентность правок, обратимость, append-only audit log, изоляция сбоев батча.
- **NFR-5 (производительность).** Probe — async batch (Celery + Redis); аудит сайта в пределах целевого SLA по числу страниц.
- **NFR-6 (vector).** pgvector на старте (cloud); Qdrant — позже для нагрузок/on-prem (фаза C).
- **NFR-7 (трекинг).** Продуктовая аналитика (PostHog self-hosted) для North Star/активации с дня 1.
- **NFR-8 (trial-окно).** Длительность trial и «value window» дизайнятся так, чтобы Visibility-сдвиг был наблюдаем: Readiness — мгновенно; для Visibility — **≥ 21–30 дней** (особенно ChatGPT Search 7–21 дн). Self-serve trial может быть короче (14 дн) с Readiness как хук, но кейсы/design-партнёры ведутся в окне ≥ 30 дн.

### 9.4. Упаковка и pricing (MVP)
**Принцип:** auto-fix присутствует во **всех** тарифах (даже Starter — машиночитаемый слой на 1 сайт); гейтим **breadth, не moat**. Не демпингуем против Шпиониро (1 490 ₽).

**Tier 0 «Instant Audit» — бесплатный, no-auth** (лид-магнит). Платные тарифы доступны в двух режимах: **Manual** (без API — патчи копипастом + re-crawl верификация) и **Auto** (API+DPA — авто-применение + rollback). Авто-применение и rollback — только Auto-режим (см. §4.1).

| Параметр гейтинга | Starter | Pro | Business |
|---|---|---|---|
| Цена (ориентир из источника) | 5 990 ₽ | 14 990 ₽ | 29 990 ₽ |
| Сайтов | 1 | неск. | больше |
| CMS-коннекторы | WP | + Tilda/Bitrix (по мере A.4) | все доступные |
| Частота probe | monthly | weekly | daily |
| Глубина правок | машиночитаемый авто | + FAQ-draft/review | + расширенные |
| Модели | 4 | 4 (+ A.4) | 4 (+ A.4) |

**Trial:** full-feature, time-limited; обязательно выполняет реальный аудит + применяет первую правку (мгновенная Readiness-delta = конверсионный хук).

### 9.5. GTM (MVP) — последовательность, не «всё сразу»
1. **Мес. 1–6:** 5–10 design-партнёров (white-glove) → сбор evidence → **2–3 кейс-стади** (vc.ru, Habr, Telegram).
2. Founder-led контент + комьюнити (спрос «67% хотят практические кейсы»), выступления (Optimization, RSEO Conference, RIW).
3. **После накопления кейсов** — performance (Я.Директ + VK Реклама + Product Hunt RU / СтартПак).
4. Agency/Yandex Cloud/Сбер-партнёрства — инструмент фазы B.

### 9.6. Команда (staffing constraint)
Из источника (условие успеха): 2 backend (Python/FastAPI), 1 frontend (Next.js/TS), 1 ML/контент-инженер, 1 founder/PM. **Обязательно: 2 контент/SEO-эксперта в команде ИЛИ advisor-board** (идеальный профиль advisor — ex-руководитель GEO-направления крупного SEO-агентства). Это не чисто tech-проект.

### 9.7. Критерии завершения MVP = A→B gate (см. §8).

---

## 10. ФАЗА 2 — Сценарий B: Agency white-label (рамочно)

**Цель:** платформа для SEO/SERM-агентств, продающих GEO под своим брендом; дифференциация от Шпиониро — auto-fix + качество CMS-интеграций.

**Ключевой scope (уточняется на gate):**
- Multi-tenant: аккаунт агентства → N клиентских сайтов; роли agency admin / agency seo / client viewer.
- White-label кабинет (домен, лого, цвета, footer).
- Agency-billing (счета на агентство, договоры с НДС, РФ-юрлицо).
- Bulk-операции (аудит/генерация по 50 сайтам), API для агентских интеграций.
- Отчётность (PDF/PPTX с шильдиком), competitive benchmarking, **sentiment-трекинг**, Slack/Telegram-алерты.
- Расширение CMS: WordPress, Tilda, Bitrix, 1C-Битрикс, Modx, OpenCart (+ Shopify для экспортных).
- Партнёрская программа, образовательный контент (certified GEO-specialist).

**Метрика-цель (ориентир источника):** MRR 8–12M ₽ к ~мес. 9 фазы B.

---

## 11. ФАЗА 3 — Сценарий C: Enterprise full-cycle + Integration layer (рамочно)

**Цель:** полноценная «AI Readiness Platform», единственная в РФ, закрывающая все 3 уровня.

**Ключевой scope (уточняется на gate, валидируется доп. дискавери):**
- Production-ready коннекторы: Bitrix24, 1C-Битрикс, Magento (Adobe Commerce), InSales, Shopify Plus, headless (Strapi/Contentful/Sanity); запись JSON-LD без участия разработчика клиента; staging; audit log; версионирование/rollback.
- **MCP-сервер на сайт** (@modelcontextprotocol/sdk): эндпоинты product_search / content_query / knowledge_base. *(Спрос на MCP подтверждён; «MCP на маркетинг-сайт» — валидировать.)*
- Public content API (REST + GraphQL), LLM-export endpoints, webhook content sync, **llms.txt/llms-full.txt** (его настоящий дом).
- Embeddings as a service (multilingual-e5-large, BGE-M3, Yandex/GigaChat Embeddings); Vector DB (Qdrant self-host / pgvector); semantic search API; auto-update по webhook.
- Agent-friendly forms (ARIA), product feeds (Я.Маркет, Wildberries, Ozon Seller API, Google Shopping).
- **A/B-тестирование AI-видимости** (статистический модуль).
- On-premise (Helm/K8s) для банков/госзаказа; SLA 99,9%; dedicated CSM.

**Метрика-цель (ориентир источника):** ARR через 24 мес — 60–120M ₽ (10–20 enterprise-клиентов). Суммарно по hybrid-стратегии: ~80–140M ₽ ARR (уровень pre-Series A).

---

## 12. Технологический стек (baseline-constraint для ТЗ)

Принят «boring tech» из источника без изменений (обоснован и непротиворечив).

- **Backend:** Python 3.12+, FastAPI + Pydantic v2, SQLAlchemy 2.x + Alembic.
- **Данные:** PostgreSQL 16 + **pgvector** (Qdrant позже для нагрузок/on-prem); Redis 7 (кеш, rate-limit, sessions); Celery + Redis/RabbitMQ (очереди).
- **Auth:** Keycloak (self-hosted, OIDC, multi-tenancy).
- **Frontend:** Next.js 15 (React 19), TypeScript 5.x, shadcn/ui + Tailwind, Recharts (продукт) + Plotly (отчёты), React Hook Form + Zod, Zustand / TanStack Query.
- **Crawler/probe:** Crawlee (Python) / Scrapy, Playwright (SPA), резидентные прокси (Smartproxy/Bright Data), rdflib + custom JSON-LD validator, httpx + tenacity. LLM-провайдеры probe: OpenAI, Anthropic, Yandex Cloud FM, GigaChat, Perplexity, Gemini API + scraping fallback.
- **AI/ML:** LangChain/LlamaIndex (минимально), embeddings RU (Yandex/GigaChat) + OSS (e5/BGE-M3), Qdrant/pgvector, MCP SDK (фаза C), OSS LLM fallback (vLLM + Llama 3.3 / Qwen 2.5 / Saiga).
- **CMS-коннекторы (по фазам):** WP (мес. 7) → Tilda (мес. 8) → 1C-Битрикс (мес. 9–10) → Modx/OpenCart (B) → Magento/Shopify/headless (C).
- **Инфра/DevOps:** Yandex Cloud (РФ, 152-ФЗ) + Hetzner/Selectel (зарубежный probe); Docker → Kubernetes (on-prem C); ArgoCD; GitLab CI (РФ) / GitHub Actions; Grafana+Prometheus+Loki+Tempo; Sentry; Vault / Yandex Lockbox.
- **Биллинг/compliance:** ЮKassa (РФ) + Stripe (экспорт, B); Контур.Диадок/СБИС (B2B); Mailgun/Unisender; PostHog (self-host); Intercom/Chatwoot.

---

## 13. Метрики и аналитика (детально)

- **Funnel (PLG):** число Tier 0 аудитов, конверсия Tier 0→paid (Manual/Auto), конверсия Manual→Auto upgrade.
- **Activation:** time-to-first-verified-fix, % сайтов с применённым fix, % завершивших онбординг.
- **Engagement:** активные сайты (WAU/MAU сайтов), частота probe-прогонов, число применённых правок.
- **Value:** Readiness-delta (мгновенно), Visibility/Citation-delta на retrieval-поверхностях (с полосой шума).
- **Trust:** % auto-apply opt-in по типам правок, rollback-rate, DPA-sign rate, инциденты порчи production (цель: 0).
- **Качество метрики:** Stability (внутренний разброс), доля промптов с широким CI (флаг недоверия).
- **Business:** MRR, paying sites, ARPU, M3/M6-retention, churn, CAC, LTV/CAC (≥3), payback.

---

## 14. Риски и митигации (обновлено рынком)

| Риск | Вер. | Impact | Митигация |
|---|---|---|---|
| Яндекс/Сбер запускают нативный GEO | Средняя | Высокий | Cross-platform (вкл. ChatGPT/Perplexity, которых у них не будет); CMS-интеграции = high switching cost |
| Изменение API LLM-провайдеров | Высокая | Средний | Multi-provider router; scraping fallback; пул прокси |
| Холодный старт без кейсов | Высокая | Высокий | 10 design-партнёров → кейсы; партнёрство с известным агентством; GTM cases-first |
| **Отказ давать API-доступ (риск №1 тезиса)** (уточнён) | Средняя | Высокий→Средний | **Manual track монетизирует без API** (Tier 0 + патчи копипастом + re-crawl); auto-apply — апгрейд; DPA gate только для Auto track |
| Перегрев рынка («все продают GEO») | Высокая | Средний | Продуктовый аргумент (full-cycle + auto-fix), не маркетинговый; community-marketing |
| **llms.txt-«theater»** (новый) | — | Средний | **Не позиционировать llms.txt как citation-драйвер; не весить в Score; делать ставку на schema+FAQ+авторитет** |
| **Time-to-citation длинный для не-retrieval** (уточнён) | Средняя | Средний | Таргетировать retrieval-поверхности; two-tier proof; trial/окно ≥ 21–30 дн; Readiness как мгновенный хук |
| **Скорость глобальных + капитал** (новый) | Высокая | Средний | Скорость MVP; RU-moat; мониторинг конкурентной динамики; ревизия PRD каждые 4 нед |
| Платные AI-индексы | Низкая | Высокий | Гибкая архитектура; opt-in/opt-out llms.txt; лицензионные партнёрства |
| Недетерминированность LLM-метрик | Высокая | Средний | N≥5 probe; CI; Stability/Coverage; доктрина honest uncertainty |
| Медленная разработка CMS-коннекторов | Средняя | Высокий | Приоритет по write-доступу (WP первым); webhooks вместо native на старте |
| Юр-чувствительность auto-fix | Средняя | Высокий | DPA с дня 1; audit log; rollback; staging для видимого контента |

---

## 15. Compliance и юридическое
- 152-ФЗ заложен в архитектуру (NFR-1); on-premise опция (фаза C).
- DPA на авто-правки — обязательное условие активации auto-fix (FR-4.6).
- Контент клиента по умолчанию обрабатывается RU-моделями (NFR-3).
- Append-only audit log как доказательная база изменений (FR-4.4).

---

## 16. Открытые вопросы и гипотезы к валидации
1. **(Phase 0 / H1–H5)** доступ к сайту, willingness-to-pay за auto-fix, переход агентств, time-to-citation, DPA — go/no-go для тяжёлого auto-fix.
2. **Достоверность вход-цифр.** Множители конверсии AI-трафика (4–14×, «+6 432% YoY») и доля ChatGPT 54,1% — относиться как к ориентиру; перепроверить на собственных данных, не закладывать в обещания клиентам.
3. **AI-Readiness Score — состав весов.** Зафиксировать так, чтобы Score коррелировал с реальной Visibility (исключить llms.txt из citation-веса; калибровать по фактическим citation-данным).
4. **Retrieval-поверхности РФ.** Точная механика и time-to-citation Яндекс Нейро/Алисы на новый контент (RAG-цикл) — замерить.
5. **MCP-на-маркетинг-сайт (фаза C).** Реальный спрос — отдельный дискавери.
6. **Длительность trial vs наблюдаемость Visibility** — финализировать (14 vs 21 vs 30 дн) по данным Phase 0 (H4).
7. **Порог auto-apply (trust ladder)** — какие именно типы машиночитаемых правок дефолтно разрешать в авто после скольких успешных approve.
8. **Конверсия воронки Tier 0 → Manual → Auto** — целевые коэффициенты, где основной upsell в Auto track, цена Manual vs Auto.
9. **Предиктивная Visibility-модель** — порог накопленных before/after данных (из Auto track) для перехода от индустриальных бенчмарков к site-specific прогнозу.

---

## 17. Источники

**Исходный документ:** «AI Visibility SaaS для РФ-сегмента» v2.0, 2026-05-08 (внутренний).

**Рыночная верификация (июнь 2026):**
- llms.txt adoption: [SE Ranking](https://seranking.com/blog/llms-txt/), [AEO Engine](https://aeoengine.ai/blog/llms-txt-zero-usage-ai-bots-ignore), [Otterly](https://otterly.ai/blog/the-llms-txt-experiment/)
- Schema/structured data → AI citations: [AEO Engine](https://aeoengine.ai/blog/llm-visibility-optimization-with-structured-data-and-schema), [Search Engine Land](https://searchengineland.com/schema-markup-ai-search-no-hype-472339), [Walker Sands](https://www.walkersands.com/about/blog/how-can-schema-markup-support-llm-visibility/)
- GEO-рынок / Profound funding: [Fortune](https://fortune.com/2026/02/24/exclusive-as-ai-threatens-search-profound-raises-96-million-to-help-brands-stay-visible/), [Omnius AI Search & GEO Report 2026](https://www.omnius.so/blog/ai-search-geo-report-and-trends-2026)
- MCP adoption: [Digital Applied](https://www.digitalapplied.com/blog/mcp-adoption-statistics-2026-model-context-protocol), [MCP 2026 Roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/)
- Time-to-citation: [Leapd](https://www.leapd.ai/blog/ai-visibility/how-chatgpt-google-ai-overviews-and-perplexity-source-information-in-2026), [Profound — citation patterns](https://www.tryprofound.com/blog/ai-platform-citation-patterns)
- РФ-рынок GEO/AEO: [vc.ru — рейтинг GEO-агентств 2026](https://vc.ru/marketing/2924772-reiting-top-10-geo-agentstv-rossii), [Sostav](https://www.sostav.ru/blogs/291085/90969), [Habr — гайд GEO/AEO 2026](https://habr.com/ru/articles/1042732/)

---

*Документ — draft v0.2. Изменения v0.2: добавлены Tier 0 Instant Audit (no-auth) + Manual/Auto tracks (read-only first), честная модель прогноза, competitive gap, re-crawl верификация (§4.1, FR-3.3–3.5, FR-4.7, FR-5.5). Ревизия каждые 4 недели. Следующий шаг: прохождение Phase 0 → уточнение MVP-требований → ТЗ.*
