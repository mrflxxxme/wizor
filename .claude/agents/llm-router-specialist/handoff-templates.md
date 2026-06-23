# llm-router-specialist — handoff templates (charter §8.6)

## Outbound → backend-implementer (после P4)

```
### HANDOFF llm-router-specialist → backend-implementer · P4 · <ISO-ts>
- task: интеграция LLM-router в FastAPI
- did: router.py + адаптеры GigaChat/YandexGPT/vLLM; fallback-цепочки; RU-default верифицирован
- artifacts: [src/llm_router/router.py, src/llm_router/adapters/, src/llm_router/config.yaml]
- contracts_touched: [llm-router]
- self_audit: pass  (ПДн → только RU; нет хардкода ключей; LangChain минимален)
- next: backend-implementer подключает router к FAQ-gen и probe
- escalate: none
```

## Outbound → compliance-152fz-specialist (запрос вердикта)

```
### HANDOFF llm-router-specialist → compliance-152fz-specialist · <phase> · <ISO-ts>
- task: compliance-вердикт по провайдеру [Имя]
- did: адаптер реализован; требуется разрешение на использование
- artifacts: [src/llm_router/adapters/provider.py]
- contracts_touched: [llm-router]
- self_audit: pass
- next: compliance-152fz-specialist: COMPLIANT / NON-COMPLIANT
- escalate: none
```
