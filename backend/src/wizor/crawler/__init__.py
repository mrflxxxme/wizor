"""Crawler / Аудит контекст (P2, read-only).

Read-only краул сайта клиента + schema-валидатор. Единственная точка входа для
backend-слоя — `audit_site` (см. `audit.py`). Инвариант §6.1: ноль write-операций
на внешние домены (только HTTP GET; enforcement — `guard.py`).
"""
