"""Probe контекст (P5, read-only).

Dual-geo probe-мониторинг 4 LLM-моделей (Алиса/Яндекс, GigaChat — RU-ноды; ChatGPT,
Perplexity — зарубежные ноды + прокси). Инвариант §6.4: ни один probe к ChatGPT/
Perplexity не идёт с РФ-IP. N≥5 прогонов на промпт×модель; агрегация с CI (переиспользует
`llm_router.uncertainty`). Данные — основа для P6 (рекомендации) и P8 (верификация).
DTO-шов — `schemas.py`.
"""
