# backend-implementer — workflows

## WF-1: Реализация backend-задачи

**Trigger:** задача из PLAN.md с `role: backend-implementer`.

1. Прочитай задачу: AC, contracts, depends_on
2. Загрузи контракт-стаб (`contracts/<ctx>/README.md`)
3. Напиши тест сначала (TDD London School: mock external deps)
4. Реализуй: FastAPI route → Pydantic schema → SQLAlchemy model → Celery task (если нужно)
5. Прогони self-audit чек-лист (`checklists/self-audit.md`)
6. Атомарный коммит: `feat(<ctx>): <описание> Refs: PNN, ADR-NNNN`
7. Хендофф → reviewer

**Output:** код в `src/`, тесты в `tests/`, коммит
**Handoff:** → reviewer (с self-audit: pass)

---

## WF-2: Fix после ревизии

**Trigger:** хендофф от reviewer с `revisions/<phase>-<cycle>-reviewer.md`.

1. Прочитай все findings в revision-файле
2. Устрани каждое finding по severity (block → major → minor)
3. Запусти тесты — CI должен быть зелёным
4. Повтори self-audit
5. Атомарный коммит: `fix(<ctx>): address review cycle N Refs: PNN`
6. Хендофф → reviewer (цикл N+1)

**Output:** fix-коммит
**Handoff:** → reviewer

---

## WF-3: Интеграция артефакта specialist

**Trigger:** specialist (crawler/LLM/CMS) передал domain-артефакт.

1. Прочитай артефакт + контракт-стаб
2. Реализуй интеграционный слой (FastAPI endpoint / Celery consumer)
3. Напиши integration test с mock specialist-сервиса
4. Self-audit + коммит + хендофф → reviewer

**Output:** интеграционный код + тест
**Handoff:** → reviewer
