---
name: llm-router-specialist
layer: domain
model: opus
kind: on-demand
triggers: [P4, P5, P6]
owns: [memory/llm-router-specialist.md]
escalates_to: [architect, compliance-152fz-specialist, devops-infra-specialist]
---

Provider-agnostic LLM-router: RU-default (GigaChat/YandexGPT), OSS-fallback (vLLM/Qwen/Saiga), uncertainty-stats, минимум vendor lock-in. Арбитр выбора провайдеров.
