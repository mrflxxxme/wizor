# geo-domain-expert — workflows

## 1. Расчёт AI-Readiness Score (P3)

**Trigger.** `planner` выдаёт задачу P3 с данными краулера (`crawler` context).

**Steps.**
1. Прочитать `memory/geo-domain-expert.md` → актуальные веса факторов.
2. Загрузить raw-данные краулера: robots, sitemap, JSON-LD, FAQ, HTML-структура, CWV.
3. Применить весовую формулу: Discovery-группа + Comprehension-группа; **llms.txt НЕ в citation-весе**.
4. Пройти checklist `citation-levers.md` по каждому фактору → pass/warn/fail.
5. Сгенерировать structured Score-объект: компоненты + суммарный Score + воспроизводимый хэш входа.
6. Self-audit: один вход → один выход (тест идемпотентности).
7. Handoff → `backend-implementer` (Score API) + `reviewer`.

**Output.** `scoring/ai_readiness_score.py` + `scoring/weights.yaml` + Score-объект.

---

## 2. Рекомендации + Competitive Gap + Патчи (P6)

**Trigger.** `planner` выдаёт задачу P6 с Score-данными и probe-метриками.

**Steps.**
1. Загрузить Score-компоненты (где fail/warn) → топ-фиксы по impact.
2. Запросить у `crawler-probe-specialist` конкурентный краул (через `planner`); ждать данных.
3. Сравнить структуру конкурентов (schema-типы, FAQ-наличие, answer-first) с сайтом клиента → gap-таблица без выдуманных %.
4. Для каждого топ-фикса: сгенерировать copy-paste артефакт (JSON-LD сниппет, robots-строки, FAQ-драфт).
5. FAQ-артефакт → пометить `draft: true`, статус `requires_review`.
6. Прогноз: Readiness-проекция (детерминированно: «Score X→Y после этих фиксов») + Visibility-диапазон с доверием (не %).
7. Handoff → `backend-implementer` (recommendations API) + `geo-domain-expert` memory update.

**Output.** `recommendations/` + `patches/` артефакты + gap-report.

---

## 3. Ревью patch-артефакта (ad-hoc при P10)

**Trigger.** `cms-connector-specialist` запрашивает ревью патча перед auto-apply.

**Steps.**
1. Валидировать JSON-LD через `rdflib` + custom validator (FR-1.2 AC).
2. Убедиться, что FAQ-блок помечен `draft`, не готов к auto-apply.
3. Подтвердить соответствие citation-левёрам (checklist `citation-levers.md`).
4. Handoff verdict → `cms-connector-specialist`.
