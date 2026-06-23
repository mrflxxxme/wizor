# crawler-probe-specialist — handoff templates (charter §8.6)

## Outbound → geo-domain-expert (после краула P2)

```
### HANDOFF crawler-probe-specialist → geo-domain-expert · P2 · <ISO-ts>
- task: передача данных аудита для Score
- did: N страниц; SPA-рендер: ok/failed; данные структурированы
- artifacts: [crawler/site_audit_{tenant_id}_{ts}.json]
- contracts_touched: [crawler]
- self_audit: pass
- next: geo-domain-expert рассчитывает Score
- escalate: none | spa_render_failed — требует Playwright-отладки
```

## Outbound → backend-implementer (probe-результаты P5)

```
### HANDOFF crawler-probe-specialist → backend-implementer · P5 · <ISO-ts>
- task: передача probe-результатов в metrics context
- did: N≥5×4 модели; CI рассчитан; dual-geo: IP-проверка пройдена
- artifacts: [probe/results_{tenant_id}_{ts}.json]
- contracts_touched: [probe, metrics]
- self_audit: pass  (нет RF-IP для ChatGPT/Perplexity; батч-сбои залогированы)
- next: backend-implementer сохраняет; geo-domain-expert интерпретирует
- escalate: none | low_confidence — CI слишком широк, нужно ↑N
```
