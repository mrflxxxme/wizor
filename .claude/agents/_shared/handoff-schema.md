# WIZOR — handoff schema

> **Формат:** компактный markdown-блок (charter §8.6, ADR-0004). **НЕ** CloudEvents-JSON (тот формат тяжёл и не нужен для файл-нативного харнесса). Хранится в `HANDOFF.md` (≤2 KB снапшот) + логируется в `JOURNAL.md`.

## Канонический формат

```
### HANDOFF <from> → <to> · <phase-id> · <ISO-ts>
- task: <одна строка — что именно передаётся>
- did: <ключевое что сделано (1–2 строки)>
- artifacts: [<файл1>, <файл2>]
- contracts_touched: [<context1>, <context2>]
- self_audit: pass | fail  (<причина при fail> + ссылка на checklist)
- next: <следующее действие получателя>
- escalate: none | <причина + вопрос для эскалации>
```

## Правила заполнения

| Поле | Обязательность | Норма |
|---|---|---|
| `from → to` | ВСЕГДА | имена ролей из charter §3 |
| `phase-id` | ВСЕГДА | `P2`, `P3`, ... или `P10` |
| `ISO-ts` | ВСЕГДА | `2026-06-23T14:05:00Z` |
| `task` | ВСЕГДА | одна строка, конкретная |
| `did` | ВСЕГДА | что реально сделано, не «работал над» |
| `artifacts` | если есть | абсолютные пути или repo-relative |
| `contracts_touched` | если есть | bounded context из charter §7 |
| `self_audit` | ВСЕГДА | `pass` или `fail` с причиной |
| `next` | ВСЕГДА | конкретное действие, не «продолжить» |
| `escalate` | ВСЕГДА | `none` явно, или причина + вопрос |

## Валидационные правила

1. **`self_audit: fail` + `escalate: none`** — невозможная комбинация: если self-audit упал, всегда указать причину в `escalate`.
2. **`artifacts`** — файлы должны существовать к моменту handoff (не «будут созданы»).
3. **`contracts_touched`** — только имена из charter §7 (13 bounded contexts).
4. **Размер HANDOFF.md** — не более 2 KB (только последний снапшот; история → JOURNAL.md).
5. **Хранение** — `memory-curator` единственный, кто обновляет `HANDOFF.md`; агенты пишут handoff-блок в свой рабочий файл, `memory-curator` переносит.

## Пример: specialist → implementer

```
### HANDOFF geo-domain-expert → backend-implementer · P3 · 2026-07-01T10:30:00Z
- task: интеграция AI-Readiness Score в FastAPI endpoint
- did: реализован scoring/ai_readiness_score.py + weights.yaml; Score воспроизводим; llms.txt НЕ в citation-весе
- artifacts: [src/scoring/ai_readiness_score.py, src/scoring/weights.yaml]
- contracts_touched: [scoring]
- self_audit: pass  (citation-levers.md пройден)
- next: backend-implementer оборачивает в POST /api/v1/audit/score
- escalate: none
```

## Пример: escalate

```
### HANDOFF crawler-probe-specialist → devops-infra-specialist · P5 · 2026-07-05T16:00:00Z
- task: зарубежные probe-ноды недоступны
- did: probe-батч запущен; 0/3 зарубежных нод ответили; RF-ноды работают
- artifacts: [logs/probe-error-2026-07-05.json]
- contracts_touched: [probe]
- self_audit: fail  (dual-geo инвариант нарушен — нет зарубежных нод)
- next: devops-infra-specialist диагностирует и восстанавливает ноды
- escalate: nodes_unavailable — все Hetzner/Selectel ноды не отвечают; probe к ChatGPT/Perplexity невозможен
```
