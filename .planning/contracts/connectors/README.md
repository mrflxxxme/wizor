# Context: `connectors` — CMS Connectors

**Purpose:** Применяет патчи на сайт через CMS-интеграции. MVP: WordPress-коннектор (custom plugin → WP REST API). Записывает JSON-LD в `<head>`, обновляет robots.txt, генерирует/публикует llms.txt/llms-full.txt, выполняет IndexNow-пинг. Все операции идемпотентны и обратимы. Активируется только после акцепта DPA и в рамках Auto track. FAQ-блоки (видимый контент) — только через review/merge-flow, не напрямую.

**Owns (data):** Конфигурации подключений (CMS endpoint, credentials — зашифровано), история применённых операций (что, когда, diff), статус каждой операции.

**Track:** auto

**Exposes (API):** [STUB — api.yaml заполняется JIT при планировании P10]

**Emits (events):** [STUB — events.yaml JIT]

**Depends on:** patches

**Schema:** [STUB — schema.sql JIT]

**Invariants:**
- **§6 инвариант 1** — Коннектор активируется только в Auto track (DPA акцептован); Manual track использует только `patches`-артефакты для ручного применения.
- **§6 инвариант 3** — Все операции идемпотентны (повторное применение безопасно) и обратимы (rollback через `autofix`); каждая операция пишется в append-only audit log до исполнения.
- **§6 инвариант 10** — Видимый контент (FAQ-блоки) **никогда** не применяется автоматически через коннектор; только review/merge-flow.
- Credentials CMS хранятся зашифрованными (Vault / Yandex Lockbox); plaintext не логируется (§6 инвариант 9).

**Phase refs:** P10 (WP-коннектор + auto-fix, gated by P0 и P9).
