# invariant-checklist (auditor)

10 стоячих инвариантов из charter §6. Проверять в КАЖДОМ аудите.

| # | Инвариант | Проверка | Статус |
|---|-----------|----------|--------|
| 1 | **Read-only-граница:** Tier0/Manual — ноль write/API-вызовов; DPA/API — гейт ТОЛЬКО Auto track | grep write-ops в Tier0/Manual коде | [ ] |
| 2 | **Honest forecast:** нигде нет гарантированного Visibility-%; всегда диапазон+доверие | grep "гарантируем" / "100%" | [ ] |
| 3 | **Auto-fix safety:** идемпотентность + обратимость + append-only audit log; DPA до авто-правки | проверить autofix-код (если есть) | [ ] |
| 4 | **Probe-гео:** ни один probe к ChatGPT/Perplexity не с РФ-IP | проверить probe-конфиг и geo-routing | [ ] |
| 5 | **llms.txt** НЕ весит в citation/Readiness Score | проверить scoring-логику | [ ] |
| 6 | **ПДн-резидентность:** ПД клиентов в РФ (Yandex Cloud); контент RU-модели по умолчанию | проверить storage config и LLM-routing | [ ] |
| 7 | **Uncertainty:** улучшение Visibility — только вне полосы шума (N≥5+CI) | проверить metrics-расчёты | [ ] |
| 8 | **Multi-tenant изоляция:** `tenant_id` везде; нет cross-tenant утечки | grep tenant_id в новом коде | [ ] |
| 9 | **Secrets** никогда не в коде/коммитах | grep secrets-паттернов в diff | [ ] |
| 10 | **FAQ (видимый контент)** никогда не авто-применяется — только review | проверить autofix scope | [ ] |

**Правило:** хотя бы одно [ ] незакрытое → минимум PASS-WITH-FIXES. Инварианты 1, 3, 9 незакрытые → BLOCKED.
