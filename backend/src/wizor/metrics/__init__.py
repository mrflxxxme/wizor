"""Metrics контекст (P5, read-only).

Агрегирует probe-прогоны (context `probe`) в Visibility-метрики: Visibility Score
(композит), Coverage/Presence, Share of Voice, Citation Rate, Stability — каждая с
полосой шума (CI, N≥5, §6.7). Uncertainty заявляется только вне полосы шума (§6.2/§6.7).
DTO-шов — `schemas.py`.
"""
