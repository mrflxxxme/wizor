# geo-domain-expert — handoff templates (charter §8.6)

## Outbound → backend-implementer (P3 Score)

```
### HANDOFF geo-domain-expert → backend-implementer · P3 · <ISO-ts>
- task: интеграция AI-Readiness Score в FastAPI
- did: scoring/ai_readiness_score.py + weights.yaml; воспроизводим; llms.txt не в весе
- artifacts: [src/scoring/ai_readiness_score.py, src/scoring/weights.yaml]
- contracts_touched: [scoring]
- self_audit: pass  (citation-levers.md пройден)
- next: POST /api/v1/audit/score
- escalate: none
```

## Outbound → reviewer (P6 рекомендации)

```
### HANDOFF geo-domain-expert → reviewer · P6 · <ISO-ts>
- task: ревью recommendations + patches
- did: прио-лист; gap (evidence-based); патчи; FAQ = draft:true
- artifacts: [src/recommendations/, src/patches/, reports/gap-P6.md]
- contracts_touched: [recommendations, patches]
- self_audit: pass  (нет %; FAQ = draft; gap = доказательные разрывы)
- next: reviewer → correctness + geo-линза
- escalate: none
```

## Outbound → architect (эскалация весов)

```
### HANDOFF geo-domain-expert → architect · <phase> · <ISO-ts>
- task: веса Score требуют ADR
- did: анализ дрейфа в reports/score-drift.md
- artifacts: [reports/score-drift.md]
- contracts_touched: [scoring]
- self_audit: fail  (веса не коррелируют с данными)
- next: architect создаёт ADR-NNNN
- escalate: weights_require_adr
```
