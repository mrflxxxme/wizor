# contracts/ — Карта bounded-context'ов WIZOR

Авторитетный источник границ модулей для всех build-агентов. Каждый поддомен — отдельная папка с `README.md`-стабом. Файлы `api.yaml`, `events.yaml`, `schema.sql` **не генерируются заранее** — они заполняются JIT в момент планирования фазы, касающейся данного контекста (ADR-0008, charter §9).

---

## Карта контекстов (charter §7)

| Контекст | Назначение | Track | Зависит от |
|---|---|---|---|
| [`iam`](./iam/) | Auth (Keycloak/OIDC), multi-tenancy (`tenant_id`), entitlements дорожек Tier0 / Manual / Auto | infra | — |
| [`crawler`](./crawler/) | Краул сайта + конкурентов + re-crawl (read-only) | read-only | — |
| [`scoring`](./scoring/) | AI-Readiness Score (детерминированный, on-site) | read-only | crawler |
| [`probe`](./probe/) | LLM-probe мониторинг (dual-geo, N≥5+CI, 4 модели) | read-only | llm-router |
| [`metrics`](./metrics/) | Visibility / Coverage / SoV / Citation / Stability, uncertainty | read-only | probe |
| [`recommendations`](./recommendations/) | Прио-фиксы, competitive gap, honest forecast, FAQ-gen | read-only | scoring, metrics |
| [`patches`](./patches/) | Генерация copy-paste артефактов (JSON-LD, robots, llms.txt, FAQ-блок) | read-only | recommendations |
| [`connectors`](./connectors/) | Применение патчей через CMS (WordPress plugin) | auto | patches |
| [`autofix`](./autofix/) | Trust-ladder, audit-log, rollback, DPA-оркестрация | auto | connectors |
| [`verification`](./verification/) | Readiness-delta / Visibility-delta, evidence, re-crawl-verify, алерты | read-only | scoring, metrics |
| [`llm-router`](./llm-router/) | Provider-agnostic LLM gateway, RU-default, OSS-fallback | infra | — |
| [`billing`](./billing/) | ЮKassa, тарифы, trial, entitlements дорожек | infra | iam |
| [`notifications`](./notifications/) | Email / Telegram / webhook алерты деградации | infra | — |

> **Compliance (152-ФЗ)** — сквозной инвариант, не отдельный контекст. Проверяется в каждом аудите через инварианты §6 charter (1, 3, 6, 8, 9).

---

## JIT-политика (ADR-0008)

Файлы `api.yaml`, `events.yaml`, `schema.sql` **намеренно не заполнены** на этом этапе. Они генерируются агентом `planner` или профильным специалистом в рамках фазы, которая первой касается данного контекста (колонка «Контексты» роадмапа, charter §5). До этого момента стаб `README.md` является единственным авторитетным источником назначения, владения данными, трека и зависимостей.

---

## Как агенты используют контракты

1. **Перед реализацией** — `backend-implementer` / специалист читает `README.md` целевого контекста и всех его зависимостей.
2. **Граница модуля** — контракт определяет, какой контекст владеет таблицей / событием / эндпоинтом. Агенты **не дублируют** DDL/OpenAPI/события между контекстами.
3. **При обновлении** — если фаза меняет API или схему, агент заполняет / обновляет `api.yaml` / `events.yaml` / `schema.sql` в данной папке и бампает семвер.
4. **Cross-context вызовы** — описываются явно в секции «Depends on» стаба; избыточные зависимости эскалируются к `architect`.
5. **Аудит** — `auditor` проверяет, что реализация не выходит за задекларированные в контракте границы (charter §6, инвариант 8).
