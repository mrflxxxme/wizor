<!-- HEAD-SUMMARY (≤500т): Полный 9-шаговый цикл фазы WIZOR end-to-end. Агенты на каждом шаге, роадмап read-only-first, места подключения специалистов, где пост-аудит и memory-update. Компактная диаграмма. -->

# 07-AI-TEAM-PIPELINE — 9-шаговый цикл фазы

> **Аудитория:** любой агент в любой роли. Детали ролей — в `.claude/agents/<role>/`.

## Команда (charter §3)

**Оркестратор:** founder + главная сессия (отдельный координатор не нужен).  
**Ядро (8 persistent):** `planner`/Opus · `architect`/Opus · `backend-implementer`/Sonnet · `frontend-implementer`/Sonnet · `reviewer`/Sonnet · `verifier`/Haiku · `auditor`/Opus · `memory-curator`/Haiku.  
**Профильные (6 on-demand):** `geo-domain-expert` · `crawler-probe-specialist` · `llm-router-specialist` · `cms-connector-specialist` · `compliance-152fz-specialist` · `devops-infra-specialist`.

## Роадмап (read-only-first)

```
P0(research) → P1(infra) → P2(crawler) → P3(scoring) → P4(llm-router)
→ P5(probe) → P6(recs) → P7(tier0-PLG) → P8(verify)
→ P9(auth+billing) → P10(auto-fix) [gated_by: P0]
```

Монетизация стартует на P7 (Tier 0) и P9 (Manual track). P10 — премиум-апгрейд.

## Диаграмма цикла

```
[phase-spec готов]
        │
  1 SCOPE  ─── founder+сессия: head-summary + контракты, open-questions
        │
  2 PLAN  ──── planner/Opus → PLAN.md (задачи, AC, tier, специалисты)
        │
  3 DOMAIN ─── специалист/Sonnet|Opus: сам пишет код домена [если домен затронут]
        │
  4 IMPL  ──── *-implementer/Sonnet: атомарные коммиты + self-audit
        │
  5 REVIEW ─── reviewer/Sonnet: чек-лист + контракты ≤2 цикла
        │       [>2 цикла → architect/Opus арбитраж]
  6 VERIFY ─── verifier/Haiku: acceptance-as-tests → pass|fail
        │
 ⭐7 AUDIT ─── auditor/Opus [ОБЯЗАТЕЛЬНО]
        │       риск-тир: Tier1-2→1 линза, Tier3→3, Tier4→5
        │       стоячие инварианты §6 (все 10)
        │       вердикт: PASS|PASS-WITH-FIXES|BLOCKED
        │
 ⭐8 MEM ──── memory-curator/Haiku [ОБЯЗАТЕЛЬНО]
        │       STATUS.md + HANDOFF.md + JOURNAL.md + MEMORY-INDEX.md
        │       архив аудита + регенерация README + gate-fill
        │
  9 PR+MERGE ─ tier 1-2: авто-мердж @ green CI
                tier 3+: founder explicit approve [ОБЯЗАТЕЛЬНО]
```

## Детали ключевых шагов

**Шаг 2 Plan:** pinned — не переосмысливает на ходу; 1 вызов.

**Шаг 3 Domain-build (Режим B):**  
Специалист спавнится только когда фаза касается его домена. Специалист **сам пишет** код, не передаёт implementer.
```
P1 → devops-infra-specialist      P4 → llm-router-specialist
P2 → crawler-probe-specialist     P9 → compliance-152fz-specialist
P3 → geo-domain-expert            P10→ cms-connector + compliance [gated:P0]
```

**Шаг 5 Review:** security-линза включается при флаге `security:true` или при auth/ПДн/audit-log. После 2 циклов → `architect` арбитраж.

**Шаг 7 Audit — стоячие инварианты §6 (все 10 в каждом аудите):**
1. Read-only граница (Tier 0 / Manual — ноль write-API)
2. Honest forecast (диапазон+доверие, не точное %)
3. Auto-fix safety (идемпотентность + rollback + DPA до записи)
4. Probe-geo (нет probe к ChatGPT/Perplexity с RU-IP)
5. llms.txt не в score
6. ПДн-резидентность (Yandex Cloud)
7. Uncertainty (улучшение Visibility только вне полосы шума)
8. Multi-tenant изоляция (`tenant_id`)
9. Секреты не в коде
10. FAQ — только manual review, не авто-применение

Отчёт: `_session-context/AUDIT-YYYY-MM-DD-PNN/AUDIT-REPORT.md`.

**Шаг 8 Memory-update — единственный писатель:**  
`memory-curator` пишет: STATUS / HANDOFF (≤2 KB) / JOURNAL (+ротация >300 строк) / MEMORY-INDEX / gate-fill / README-статус / архив.

**Шаг 9 PR:** tier 1–2 авто-мердж @ green CI; tier 3+ **founder explicit approve** обязателен. Подробнее: `05-PR-WORKFLOW.md`.

## Cost-control (charter §3.4)

`per_task soft $0.40 / hard $1.50` · `per_day $20/$50` · `kill_switch $300/mo` · `stagnation 30 мин → авто-стоп`.  
**Никогда fallback вниз:** `architect`, `planner`, `auditor`, `compliance-152fz`, `llm-router`, любые security/ПДн задачи.
