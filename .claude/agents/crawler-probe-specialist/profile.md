---
name: crawler-probe-specialist
layer: domain
model: sonnet
kind: on-demand
triggers: [P2, P5, P6, P8]
owns: [memory/crawler-probe-specialist.md]
escalates_to: [llm-router-specialist, devops-infra-specialist, architect]
---

Crawlee/Playwright краулер + dual-geo probe (NO RU-IP к ChatGPT/Perplexity), ротация прокси, N≥5+CI, re-crawl, конкурентный краул.
