# llm-router-specialist — workflows

## 1. Создание provider-agnostic router (P4)

**Trigger.** `planner` выдаёт задачу P4: реализовать LLM-router.

**Steps.**
1. Прочитать NFR-3 (PRD §9.3) + compliance-вердикт от `compliance-152fz-specialist`.
2. Спроектировать unified interface: `LLMRouter.complete(messages, task_type, sensitivity)`.
3. Реализовать адаптеры: GigaChat API, Yandex Cloud FM (OpenAI-compatible), vLLM (self-hosted).
4. Routing-логика: sensitivity classifier → provider selection (см. system-prompt §Routing-логика).
5. Fallback-цепочка с явными ошибками (не тихий иностранный fallback).
6. Uncertainty-метрики: entropy по distribution N прогонов, model agreement score.
7. Self-audit: проверить, что ни одна ПДн-задача не маршрутируется на иностранный провайдер.
8. Handoff → `backend-implementer` (интеграция в FastAPI) + `devops-infra-specialist` (vLLM деплой).

**Output.** `llm_router/` (router.py, adapters/, config.yaml)

---

## 2. Подключение нового провайдера (ad-hoc)

**Trigger.** `planner` или `architect` запрашивает добавление провайдера.

**Steps.**
1. Получить compliance-вердикт от `compliance-152fz-specialist` (RF-hosted или иностранный opt-in).
2. Реализовать тонкий адаптер: только HTTP-слой над API.
3. Добавить в routing-таблицу с явным `sensitivity_allowed` списком.
4. Тест: убедиться, что fallback-цепочка не нарушена.
5. Handoff → `backend-implementer` + `reviewer`.

---

## 3. Диагностика uncertainty (поддержка probe P5)

**Trigger.** `crawler-probe-specialist` запрашивает агрегацию N прогонов.

**Steps.**
1. Получить N сырых ответов провайдера.
2. Рассчитать: entropy, CI (bootstrap или Wilson), Stability.
3. Вернуть structured stats → `metrics` context.
