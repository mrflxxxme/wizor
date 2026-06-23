<!-- HEAD-SUMMARY (≤500т): Когда founder/главная сессия делегирует суб-агенту vs делает inline. Режим B (специалист пишет код своего домена). Параллелизация независимых задач. Правило verify-after-subagent. -->

# 02-DELEGATION — правила делегирования

## Когда делегировать суб-агенту

**Делегируй:** изолированная задача с чётким input → output; независимые задачи для параллелизации; профильная работа специалиста; приближение к 120 KB контекста.

**Не делегируй:** тривиальная правка (1 файл, < 50 строк) — быстрее `Edit` напрямую; архитектурное решение — суб-агент предлагает, founder/architect решают; final merge внутри фазы — автономно (CI + `reviewer` + `auditor` PASS), человек-аппрув только на гейте фазы (ADR-0017).

## Ядро: 8 агентов (charter §3)

| Агент | Модель | Когда вызывать |
|---|---|---|
| `planner` | Opus | Старт фазы: phase-spec → `PLAN.md` |
| `architect` | Opus | ADR, конфликты, арбитраж эскалаций |
| `backend-implementer` | Sonnet | Backend-задачи по `PLAN.md` |
| `frontend-implementer` | Sonnet | Frontend-задачи по `PLAN.md` |
| `reviewer` | Sonnet | После implementer; security-линза при флаге |
| `verifier` | Haiku | Acceptance-as-tests; pass/fail после review |
| `auditor` | Opus | Обязательный пост-аудит (шаг 7) |
| `memory-curator` | Haiku | Обязательный memory-update (шаг 8); единственный писатель состояния |

## Режим B: профильные специалисты (charter §3.2)

Специалист **сам пишет** код своего домена — спавнится только когда фаза касается домена:

| Специалист | Модель | Домен |
|---|---|---|
| `geo-domain-expert` | Opus | AEO/GEO/SEO, Readiness Score, честный прогноз |
| `crawler-probe-specialist` | Sonnet | Crawlee/Playwright, dual-geo probe |
| `llm-router-specialist` | Opus | Provider-agnostic роутер, RU-default, OSS-fallback |
| `cms-connector-specialist` | Sonnet | WordPress plugin/REST, идемпотентность, rollback |
| `compliance-152fz-specialist` | Opus | 152-ФЗ, ПДн, DPA, append-only audit log |
| `devops-infra-specialist` | Sonnet | Yandex Cloud, Docker, CI/CD, секреты |

## Параллелизация

Независимые задачи — **один message, все Agent-вызовы одновременно:**

```python
Agent(description="Implement /audit endpoint", subagent_type="backend-implementer",
      run_in_background=True, prompt="...")
Agent(description="Setup CI P1", subagent_type="devops-infra-specialist",
      run_in_background=True, prompt="...")
```

Не разбивай на несколько сообщений — превращает параллельное в последовательное.

## Шаблон делегирования

```
Agent(
  description="<3-5 слов>",
  subagent_type="<роль>",
  run_in_background=True,
  prompt="""
  Задача: <одна строка цели>.
  Фаза: <PNN-slug>
  Прочитай: 1) .planning/roadmap/PNN-slug.md  2) .planning/contracts/<ctx>/README.md
  НЕ загружай: другие фазы, все ADR.
  НЕ принимай архитектурные решения — верни варианты.
  Артефакты: <что должно появиться>
  Хендофф: запиши HANDOFF-блок в конце.
  """
)
```

## Правило verify-after-subagent

После возврата суб-агента — проверяй через инструменты, не на слово:

| Что | Как |
|---|---|
| Файлы созданы | `git status` или `Glob("**/*.py")` |
| Тесты прошли | `pytest` / CI |
| Контракты соблюдены | проверить стабы |
| Хендофф записан | Read последних строк отчёта |

## Автономные доп-сессии (ADR-0017)

Внутри фазы агенты автономны и сами управляют параллелизмом и контекстом — founder подключается только на гейте.

- **Параллельные задачи** → Agent tool (свежий контекст), все вызовы в одном message.
- **Полностью независимая сессия** → headless `claude -p "<scoped prompt>"` через Bash.
- **Управление контекстом** → при ~120 KB: запиши HANDOFF → продолжи в свежей сессии (не тяни переполненный контекст).

**Guardrails:** глубина спавна ≤ 2; одновременных сессий ≤ 8; cost kill-switch ($300/мес) + stagnation-kill (30 мин); каждая единица пишет HANDOFF; `memory-curator` — единственный писатель состояния.

## Anti-patterns

- **«Реши сам» суб-агенту** — вернёт generic-ответ без ADR-контекста.
- **Читать весь `.planning/`** — у суб-агента тоже token-budget; давай конкретные файлы.
- **Одна задача двум агентам** — дублирование токенов + конфликт артефактов.
- **Polling статуса суб-агента** — `run_in_background=True`, продолжай другую работу.
