<!-- HEAD-SUMMARY (≤500т): Ростер агентов WIZOR — 8 ядро + 6 профильных специалистов on-demand. Таблица: роль, модель, когда вызывается. Источник истины — BUILD-CHARTER.md §3. Специалисты спавнятся только при касании домена фазой; без вызова = 0 токенов. -->

# AGENTS.md — ростер агентов WIZOR

> **Источник истины:** `.planning/_meta/BUILD-CHARTER.md` §3 (ростер, тиринг, бюджет).
> Этот файл — 1-страничный навигатор. При противоречии — charter побеждает.

---

## Ядро (8 агентов, persistent — определены всегда)

| Агент | Модель | Мандат | Когда вызывается |
|---|---|---|---|
| `planner` | Opus | phase-spec → `PLAN.md`: атомарные задачи, AC, tier/модель, специалисты | Старт каждой фазы; ре-план при ревизии |
| `architect` | Opus | ADR, сквозные инварианты, арбитр эскалаций | ADR-моменты, конфликты, гейты |
| `backend-implementer` | Sonnet | Python/FastAPI/SQLAlchemy по контрактам + AC | Задачи backend от planner |
| `frontend-implementer` | Sonnet | Next.js/React/shadcn по контрактам + AC | Задачи frontend от planner |
| `reviewer` | Sonnet | Ревью кода; security-линза при флаге; ≤2 цикла | После implementer |
| `verifier` | Haiku | Acceptance-как-тесты + пороги гейта, бинарно | После review (при approve) |
| `auditor` | Opus | Адверсариальный пост-аудит (1/3/5 линз по tier); стоячие инварианты | ОБЯЗАТЕЛЬНО после verify |
| `memory-curator` | Haiku | Единственный писатель STATUS/HANDOFF/JOURNAL/MEMORY-INDEX; авто-README | ОБЯЗАТЕЛЬНО после audit |

---

## Профильные специалисты (6, on-demand)

Спавнятся **только** когда фаза касается домена. Иначе — 0 токенов.

| Агент | Модель | Домен | Фазы |
|---|---|---|---|
| `geo-domain-expert` | **Opus** | AEO/GEO/SEO: citation-левера, веса AI-Readiness Score, honest-forecast, competitive gap | P3, P6, P7, P10 |
| `crawler-probe-specialist` | Sonnet | Crawlee/Playwright, dual-geo probe (NO RU-IP к ChatGPT/Perplexity), N≥5+CI, re-crawl, конкурентный краул | P2, P5, P6, P8 |
| `llm-router-specialist` | **Opus** | Provider-agnostic router, RU-default (GigaChat/YandexGPT), OSS-fallback (vLLM/Qwen/Saiga), uncertainty-stats | P4, P5, P6 |
| `cms-connector-specialist` | Sonnet | WP-plugin/REST, идемпотентность, 1-click rollback, IndexNow; Auto track only | P10 |
| `compliance-152fz-specialist` | **Opus** | 152-ФЗ, ПДн-резидентность (Yandex Cloud RF), DPA-флоу, append-only audit log, РКН | P1, P9, P10 + любая задача с ПДн |
| `devops-infra-specialist` | Sonnet | Yandex Cloud + Hetzner/Selectel (probe-ноды), Docker/CI-CD, Vault/Lockbox, rate-limit Tier-0 | P1, P4, P5, P7, P9 |

---

## Когда специалист обязателен

| Если фаза затрагивает... | Вызвать |
|---|---|
| AI-Readiness Score, веса, citation-левера, FAQ-контент, competitive gap | `geo-domain-expert` |
| Краулинг сайта, probe LLM, re-crawl верификацию, конкурентный краул | `crawler-probe-specialist` |
| Подключение LLM-провайдера, роутинг, OSS self-hosted, uncertainty | `llm-router-specialist` |
| Авто-применение правок на WP (Auto track), rollback, IndexNow | `cms-connector-specialist` |
| ПДн, хостинг данных, DPA с клиентом, audit log, РКН, биллинг (ЮKassa) | `compliance-152fz-specialist` |
| Инфра (K8s, Docker, CI, secrets, зарубежные ноды, rate-limit) | `devops-infra-specialist` |

---

## Тиринг моделей

| Tier | Кто | Правило |
|---|---|---|
| **0** | — | Тривиальные механические правки → `Edit`-инструмент напрямую, без агента |
| **Sonnet** | backend/frontend/reviewer/verifier/crawler/cms/devops | Реализация, ревью, верификация; fallback-eligible при `complexity < 0.30` |
| **Opus** | planner/architect/auditor/geo/llm-router/compliance | Суждение, архитектура, compliance, Score-веса; **never-fallback** |

**Never-fallback** (Opus всегда): `architect`, `planner`, `auditor`, `compliance-152fz-specialist`, `llm-router-specialist` (суждение), `geo-domain-expert` (Score/forecast), любые security/ПДн задачи.

---

## 9-шаговый цикл фазы (сводка)

```
1. Scope (founder) → 2. Plan (planner/Opus) → 3. Domain-build (specialist, если нужен)
→ 4. Implement (*-implementer/Sonnet) → 5. Review (reviewer/Sonnet, ≤2 цикла)
→ 6. Verify (verifier/Haiku) → 7. ★ Post-audit (auditor/Opus, ОБЯЗАТЕЛЬНО)
→ 8. ★ Memory-update (memory-curator/Haiku, ОБЯЗАТЕЛЬНО) → 9. PR + founder-approve
```

**Pipeline-шаблоны:** `.claude/agents/_shared/pipeline-templates/`
- `read-only-feature.yaml` — P2/P3/P5/P6/P7/P8
- `auto-track-feature.yaml` — P10 (gated: P0 gate)
- `infra-feature.yaml` — P1/P4/P9

**Бюджет:** `.claude/agents/_shared/cost-budget.yaml` (per-task soft $0.40 / hard $1.50; kill $300/мес).

**Handoff-формат:** `.claude/agents/_shared/handoff-schema.md` (компактный markdown-блок, не JSON).
