<!-- HEAD-SUMMARY (≤500т): Словарь WIZOR. Продуктовые: AI-Readiness Score, Visibility/Coverage/SoV/Citation Rate/Stability, Readiness-delta/Visibility-delta, retrieval surfaces, Tier 0/Manual/Auto, trust-ladder, DPA, dual-geo probe, competitive gap, honest forecast, re-crawl verification, noise band/CI, llms.txt, schema/FAQ/answer-first, IndexNow, multi-tenant/tenant_id. Харнесс: phase, gate, post-audit, MEMORY-INDEX, handoff, track, tier, AUDIT-*, head-summary. -->

# Glossary — единый словарь домена WIZOR

> Не дублировать в phase-файлах — ссылаться сюда. Grep по термину.

## Продуктовые термины

| Термин | Определение |
|---|---|
| **AI-Readiness Score** | Детерминированная on-site метрика (Discovery + Comprehension). Воспроизводима. `llms.txt` не входит в citation-вес (FR-1.3). |
| **Readiness-delta** | Изменение Score до/после правки. Мгновенно. Активационный хук (FR-5.1). |
| **Visibility Score** | Вероятностная метрика присутствия в ответах LLM (N≥5 прогонов + полоса шума). Компоненты: Coverage, SoV, Citation Rate, Stability. |
| **Visibility-delta** | Сдвиг Visibility во времени. «Реальный» = за пределами полосы шума (FR-5.2). |
| **Coverage / Presence** | Доля промптов, где сайт упомянут хотя бы раз. |
| **Share of Voice (SoV)** | Доля упоминаний сайта среди всех источников по промптам. |
| **Citation Rate** | Доля промптов, где сайт дан как источник (ссылка), — отдельно от упоминания. |
| **Stability** | Внутренний разброс при повторных прогонах. Низкая = флаг недоверия. |
| **Noise band / CI** | Доверительная полоса вокруг Visibility (N≥5 + CI). Сдвиг внутри = не заявляется. |
| **Retrieval surfaces** | LLM с live-RAG: ChatGPT Search, Perplexity, Яндекс Нейро/Алиса, Gemini AIO. |
| **Tier 0 — Instant Audit** | URL → Score + competitive gap + copy-paste патчи + базовая Visibility. No-auth (PRD §4.1). |
| **Manual track** | Дорожка без API: мониторинг + рекомендации + патчи копипастом + re-crawl. DPA не нужен. |
| **Auto track** | Дорожка с API + DPA: авто-применение + rollback. Апгрейд, не порог входа. |
| **Trust ladder** | Approval-gate по умолчанию → opt-in auto по типу правки. Видимый контент (FAQ) — никогда в auto (FR-4.2). |
| **DPA** | Data Processing Agreement. Подписывается до первой авто-правки (FR-4.6). |
| **Dual-geo probe** | RU-ноды (GigaChat/Алиса) + зарубежные ноды + прокси (ChatGPT/Perplexity). Нет probe к ChatGPT/Perplexity с РФ-IP (NFR-2). |
| **Competitive gap** | Краул конкурентов, которых цитируют LLM; конкретные структурные отличия без выдуманных % (FR-3.3). |
| **Honest forecast** | (1) Readiness-проекция — детерминировано; (2) competitive gap — evidence; (3) Visibility-% — только диапазон + доверие. Никаких гарантий (FR-3.5). |
| **Re-crawl verification** | Повторный краул → подтверждение правки в HTML. Работает без API (FR-5.5). |
| **llms.txt** | Файл для AI-агентов/IDE (Integration layer). Не весит в Score. Не citation-драйвер (PRD §7.1). |
| **Schema / JSON-LD** | Schema.org в `<head>`. Основной citation-левер. Генерируется и валидируется (FR-1.2, 4.1). |
| **FAQ / answer-first** | FAQ-блоки 50–150 слов. Первичный citation-левер. Draft → review → публикация (FR-3.2, 4.3). |
| **IndexNow** | Уведомление Bing/Яндекс Вебмастер об изменениях. Авто-пинг (FR-4.1). |
| **Multi-tenant / tenant_id** | `tenant_id` с дня 1, изоляция на уровне Postgres. Нет cross-tenant утечки (FR-6.2). |
| **Two-tier proof** | Readiness (мгновенно) + Visibility (дни-недели). Первый — онбординг-хук, второй — retention. |

## Харнесс-термины

| Термин | Определение |
|---|---|
| **Phase** | Атомарная единица разработки P0–P10. 9-шаговый цикл: scope→plan→domain-build→implement→review→verify→post-audit→memory-update→PR. |
| **Gate** | Контрольная точка: hard_thresholds + deliverables + adr_delta + risks_delta + founder_signature. Формат чартер §8.5. |
| **Post-audit** | Обязательный `auditor`/Opus. Tier 1–2: 1 линза; Tier 3: 3 (correctness/security/compliance); Tier 4: 5 (+tests/architecture). |
| **MEMORY-INDEX** | Курируемая таблица `tag | topic | pointer | gist | updated`. Точка входа для recall. |
| **Handoff** | Компактный markdown-блок передачи состояния (чартер §8.6). Пишет только `memory-curator`. |
| **Head-summary** | `<!-- HEAD-SUMMARY (≤500т): ... -->` в начале каждого дока >2 KB. Читается первым. |
| **Track** | `read-only` / `auto` / `infra` / `research` — категория фазы. |
| **Tier** | Глубина пост-аудита: 1–2 лёгкий; 3 стандарт; 4 полный. |
| **AUDIT-*** | `_session-context/AUDIT-YYYY-MM-DD-<phase>/`. После merge → `archive/`. |
