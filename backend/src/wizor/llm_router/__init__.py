"""LLM-router контекст (P4, infra).

Provider-agnostic gateway для всех LLM-вызовов платформы. RU-default (GigaChat/
YandexGPT) для контента с ПД клиента (§6.6); OSS self-hosted (vLLM/Qwen/Saiga) для
batch-cost; иностранные (OpenAI/Anthropic/Perplexity/Gemini) — opt-in / probe-канал
через зарубежные ноды (§6.4, NFR-2). Ключи провайдеров — PLACEHOLDERS/Lockbox, не в
коде (§6.9). DTO-шов — `schemas.py`; единый интерфейс — `LLMRouter.complete`.
"""
