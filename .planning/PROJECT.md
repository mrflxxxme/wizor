<!-- HEAD-SUMMARY (≤500т): Обзор проекта WIZOR. Видение: сделать любой сайт комплексно доступным для ИИ-поиска и замкнуть цикл Аудит→Мониторинг→Рекомендации→Авто-имплементация→Верификация. Главный moat: авто-имплементация + покрытие RU-стека (Алиса/Нейро, GigaChat). Three-track: Tier 0 (no-auth PLG), Manual (без API), Auto (API+DPA). 11 фаз P0–P10. Команда: solo-founder + AI-агенты + content/SEO advisor. North Star: Verified AI-Readiness Uplift. -->

# PROJECT.md — обзор проекта WIZOR

## Видение

Сделать любой сайт **комплексно доступным для ИИ** — для retrieval-пайплайнов LLM, для AI-агентов и для embedding-сервисов — и довести это до измеримого результата автоматически, замыкая полный цикл:

**Аудит → Мониторинг → Рекомендации → Авто-имплементация → Верификация**

Продукт нацелен на российский рынок, покрывает RU-стек (Алиса/Нейро, GigaChat), соответствует 152-ФЗ.

## Категория и USP

**Категория:** AI Readiness Platform (не «GEO-инструмент»; шире, защитимее, обосновывает enterprise-цены).

**Главный дифференциатор (moat):** автоматическая имплементация изменений на стороне сайта — этого не делает ни один РФ-игрок. Все конкуренты заканчиваются на «вот рекомендация → внедрите сами».

**Второй слой защиты:** покрытие RU-стека (Алиса/Нейро, GigaChat), с которым не работает ни один глобальный сервис.

**Стратегический принцип:** дифференциация достигается **не выбором технологий, а интеграционным слоем** (CMS-коннекторы, MCP-сервер, embedding-pipeline). Инженерный фокус — здесь.

## Three-track access model (read-only-first)

| Дорожка | Доступ | Что входит | Монетизация |
|---|---|---|---|
| **Tier 0 — Instant Audit** | URL, no-auth | Score + competitive gap + copy-paste патчи + базовая Visibility | Бесплатно (PLG, лид-магнит) |
| **Manual track** | Без API (read-only) | + мониторинг, прио-рекомендации, патчи копипастом, re-crawl верификация | Платно (без write-доступа) |
| **Auto track** | API + DPA | + авто-применение машиночитаемого слоя, FAQ review, rollback, closed-loop | Премиум (moat + data-flywheel) |

DPA/API — gate только Auto track, а не входа в продукт.

## Фазовый роадмап (P0–P10)

| Фаза | Название | Track | Tier |
|---|---|---|---|
| **P0** | Discovery & De-risking (H1–H5) | research | — |
| **P1** | Foundation (repo/CI, multi-tenant, Keycloak, observability) | infra | 4 |
| **P2** | Crawler / Аудит | read-only | 3 |
| **P3** | AI-Readiness Score | read-only | 3 |
| **P4** | LLM-router (provider-agnostic, RU-default) | infra | 4 |
| **P5** | Probe-мониторинг (dual-geo, N≥5+CI) | read-only | 3 |
| **P6** | Рекомендации + competitive gap + честный прогноз | read-only | 3 |
| **P7** | ⭐ Tier 0 Instant Audit (no-auth PLG) | read-only | 3 |
| **P8** | Верификация (re-crawl, deltas, evidence, алерты) | read-only | 3 |
| **P9** | Auth + биллинг + онбординг + дорожки | infra | 4 |
| **P10** | ⭐ Auto track: WP-коннектор + auto-fix + DPA | auto | 4 |
| → | **A→B gate** | — | — |

P7 + P9 (Manual track) монетизируются до Auto-fix. **P10 gated by P0** (5 гипотез H1–H5).

## Стек (one-liner)

Python 3.12 / FastAPI / Pydantic v2 / SQLAlchemy → Postgres 16+pgvector / Redis 7 / Celery → Keycloak → Next.js 15 / React 19 / shadcn → Crawlee+Playwright → LLM-router (GigaChat/YandexGPT RU-default) → Yandex Cloud (РФ, 152-ФЗ) + Hetzner/Selectel (probe) → ЮKassa → PostHog. Полный стек: [`_meta/stack.md`](./_meta/stack.md)

## Команда (PRD §9.6)

**Solo-founder** + **AI-агенты** (8 ядро + 6 профильных) + **content/SEO advisor** (обязателен — ex-руководитель GEO-направления). Без domain-expertise в GEO/AEO весовые коэффициенты Score и приоритизация рекомендаций будут неверными.

## North Star

**Verified AI-Readiness Uplift** — число сайтов, на которых применён ≥1 auto-fix **и** зафиксирована положительная Readiness-delta (вне полосы шума).

- **Активационная под-метрика:** `time-to-first-verified-fix` < 24 ч (self-serve).
- **Guardrail:** Visibility/Citation uplift на retrieval-поверхностях (медленный, долгосрочный).

## Ключевые документы

- [`PRD.md`](./PRD.md) — requirements v0.2: видение, JTBD, FR+AC, стек, team
- [`_meta/BUILD-CHARTER.md`](./_meta/BUILD-CHARTER.md) — харнесс: агенты, цикл, форматы
- [`_meta/stack.md`](./_meta/stack.md) — стек (source of truth)
- [`_meta/conventions.md`](./_meta/conventions.md) — код-стиль, CI, DoD
- [`_meta/glossary.md`](./_meta/glossary.md) — словарь домена
- [`OPEN-QUESTIONS.md`](./OPEN-QUESTIONS.md) — открытые гипотезы (PRD §16)
- [`PLACEHOLDERS.md`](./PLACEHOLDERS.md) — TBD-токены для prod
- [`gates/`](./gates/) — P0-to-heavy-autofix, A-to-B
- [`decisions/`](./decisions/) — ADR log
- [`contracts/`](./contracts/) — bounded-context контракты
