# AUDIT · P3 · линза COMPLIANCE (стоячие инварианты §6) · 2026-07-05

## #5 llms.txt НЕ весит в Score — headline-инвариант P3 — **PASS**

Задача аудита: доказать, что llms.txt структурно НЕ может повлиять на Score.

**Тройная защита (`weights.py`):**
1. Структурное отсутствие: `WEIGHTS` не содержит `llms_txt`; движок джойнит вход ТОЛЬКО с
   `WEIGHTS` (`engine.py:82`) → сигнал llms.txt в `audit_summary` никогда не читается.
2. Сторож `EXCLUDED_FROM_SCORE = ("llms_txt",)` (`weights.py:268`) — grep-якорь + чек.
3. Импорт-тайм `_verify_weight_model()` (`weights.py:272-290`, `raise` не `assert` → переживает
   `python -O`): падает, если сумма весов ≠ 100 ИЛИ если исключённый фактор попал в `WEIGHTS`.

**Попытки взлома (адверсариальный прогон):**
- Подать `llms_txt` с вердиктом pass/warn/fail/deferred в `audit_summary` → Score НЕ меняется
  (base 0.0 → все варианты 0.0).
- Алиасы `llms.txt`, `LLMS_TXT`, `llmstxt`, `llms`, `LLMs.txt` → Score НЕ меняется (ни один
  не в `WEIGHTS`).
- `llms_txt` НИКОГДА не среди компонентов (проверено программно).
- Инъекция `FactorWeight("llms_txt", 10, ...)` в `WEIGHTS` → guard кидает
  `RuntimeError` (сумма 110≠100).
- **Ключевое — non-vacuous EXCLUDED-чек:** ребаланс весов до суммы ровно 100 + `llms_txt`
  weight 10 → guard всё равно кидает `"фактор 'llms_txt' запрещён в Score (charter §6.5 /
  FR-1.3)"`. То есть EXCLUDED-проверка ловит инвариант НЕЗАВИСИМО от суммы весов.

**AC-2-тест non-vacuous:** `test_scoring_llms_invariant.py` покрывает (a) llms_txt не компонент,
(b) добавление сигнала не меняет Score, (c) сильные FAQ/schema без llms.txt СТРОГО > сильный
llms.txt при слабых FAQ/schema (`assert _score(site_a) > _score(site_b)`). Тест провалится, если
llms.txt начнёт весить. **Сконструировать вход, где llms.txt меняет Score, невозможно → PASS.**

## #2 Honest-forecast — **PASS**
- Score детерминирован (не гарантия) — ✔ по дизайну.
- `ProjectionEngine`: `delta_score`/`new_score` — детерминированный ПЕРЕСЧЁТ Score с патчем
  (`projection.py:79-110`), НЕ обещание Visibility-uplift. Docstring прямо: «детерминированный
  пересчёт сигнала готовности, НЕ гарантия Visibility-%».
- `WEIGHTS.md` (интро + §3 + §5): «Score — сигнал готовности, а не гарантия цитирования»;
  внешние числа (×2.5, +44%) явно помечены «направленное свидетельство, не гарантия для
  конкретного сайта». User-facing `description` использует «шанс»/механизм, без гарантированного %.
- Никаких полей/формулировок с «гарантируем»/«100% Visibility». **PASS.**

## #1 Read-only-граница — **PASS (satisfied)**
- P3 — чистый compute: читает `crawler.crawl_results`, пишет ТОЛЬКО собственную `score_results`.
  Ноль внешних API-вызовов, ноль записи в клиентские ресурсы.

## #8 Multi-tenant — **PASS** (детали в lens-security).
## #9 Secrets — **PASS** (pure compute, grep диффа чист).

## N-A инварианты (нет соответствующей поверхности в P3)
- **#3 Auto-fix safety** — N-A: в P3 нет autofix (фаза P10).
- **#4 Probe-гео** — N-A: в P3 нет probe (фаза P5); ноль внешних вызовов.
- **#6 ПДн-резидентность** — N-A: scoring не обрабатывает ПДн (только вердикты факторов);
  резидентность хранилища — инфра-конфиг (P1/Yandex Cloud), не код P3.
- **#7 Uncertainty (N≥5+CI)** — N-A: Score — детерминированная on-site метрика, не probe-
  измерение Visibility; полоса шума/CI относится к P5.
- **#10 FAQ авто-применение** — N-A: FAQ здесь только read-only скорится как фактор; авто-
  применения контента нет.

**Вывод линзы: PASS.**
