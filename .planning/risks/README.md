# Реестр рисков — WIZOR

Ведут `architect` + `memory-curator`; гейты ссылаются на `R-NN` через `risks_delta`. Источник и динамика — PRD §14.

| ID | Риск | Вер. | Impact | Митигация | Статус |
|---|---|---|---|---|---|
| R-1 | Отказ давать API-доступ (риск №1 тезиса) | Средняя | Средний | Manual track монетизирует без API (read-only-first); DPA — гейт только Auto track | open |
| R-2 | Юр-чувствительность auto-fix | Средняя | Высокий | DPA + append-only audit log + rollback с дня 1; P10 `gated_by` P0 | open |
| R-3 | Яндекс/Сбер запускают нативный GEO | Средняя | Высокий | Cross-platform (ChatGPT/Perplexity) + CMS-интеграции = switching cost | open |
| R-4 | Холодный старт без кейсов | Высокая | Высокий | Tier 0 лид-магнит + 10 design-партнёров → 2–3 кейса | open |
| R-5 | Скорость глобальных + капитал | Высокая | Средний | Скорость MVP; RU-moat; ревизия PRD каждые 4 нед | open |
| R-6 | Изменение API LLM-провайдеров | Высокая | Средний | Provider-agnostic router + scraping fallback + пул прокси | open |
| R-7 | Недетерминированность LLM-метрик | Высокая | Средний | N≥5 probe + CI + доктрина honest-uncertainty | open |

R-1/R-2 связаны с гейтом `gates/P0-to-heavy-autofix.md` (снятие → старт тяжёлого auto-fix, P10).
