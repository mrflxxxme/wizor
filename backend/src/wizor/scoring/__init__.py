"""Scoring контекст (P3, read-only).

Детерминированный AI-Readiness Score поверх `crawler.crawl_results.audit_summary_json`.
Веса факторов — `weights.py` (задаёт geo-domain-expert). DTO-шов — `schemas.py`.
Инвариант §6.5: `llms.txt` НЕ входит в citation-вес Score.
"""
