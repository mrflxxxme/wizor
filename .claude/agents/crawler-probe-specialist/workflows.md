# crawler-probe-specialist — workflows

## 1. Краул сайта клиента (P2)

**Trigger.** `planner` выдаёт задачу P2 с URL сайта.

**Steps.**
1. Инициализировать Crawlee-краулер: respectRobots=true (но читаем robots.txt как данные аудита).
2. Обойти сайт: собрать robots.txt, sitemap.xml, HTML всех страниц (Playwright для SPA).
3. Для каждой страницы: извлечь h1–h3, JSON-LD блоки, FAQ-маркеры, HTTP-коды, CWV.
4. Результат: structured JSON → `crawler` context.
5. Self-audit: проверить, что SPA-рендер выполнен (иначе пометить `spa_render: failed`).
6. Handoff → `geo-domain-expert` (данные для Score).

**Output.** `crawler/site_audit_{tenant_id}_{ts}.json`

---

## 2. Probe-мониторинг (P5)

**Trigger.** `planner` выдаёт задачу P5 с промпт-набором.

**Steps.**
1. Для каждого промпта × 4 модели: N≥5 прогонов.
   - Алиса/Нейро, GigaChat → RU-ноды (Yandex Cloud).
   - ChatGPT, Perplexity → зарубежные ноды (Hetzner/Selectel) + резидентные прокси. **Проверить: не RF-IP.**
2. Retry-логика: `tenacity` exponential backoff, max 3 попытки; сбой одного элемента не роняет батч.
3. Для каждого промпта: агрегировать N результатов → Visibility Score + Coverage + SoV + Citation Rate + Stability + CI.
4. Проверить: если CI слишком широк → увеличить N или пометить `low_confidence`.
5. Handoff → `metrics` context (результаты).

**Output.** `probe/results_{tenant_id}_{ts}.json` (распределения + CI)

---

## 3. Re-crawl верификация (P8, Manual track)

**Trigger.** Пользователь сообщил, что применил правку вручную; запрос re-crawl.

**Steps.**
1. Crawlee: сканировать только затронутые страницы (scope = URL-список правки).
2. Извлечь: JSON-LD в `<head>`, robots.txt, llms.txt, FAQ-блоки.
3. Сравнить с pre-patch снапшотом (из `verification` context).
4. Результат: `patch_detected: true/false` по каждому элементу.
5. Handoff → `geo-domain-expert` (пересчёт Readiness-delta).
