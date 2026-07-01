"""IAM bounded context — multi-tenancy skeleton (charter §7).

P1 — только модели данных с ``tenant_id`` (изоляция, §6.8). Полная auth
(Keycloak/OIDC, JWT-middleware, entitlements дорожек) — JIT в P9.
"""
