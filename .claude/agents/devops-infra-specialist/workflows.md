# devops-infra-specialist — workflows

## 1. Foundation-инфра (P1)

**Trigger.** `planner` выдаёт задачу P1: базовая инфраструктура.

**Steps.**
1. Получить compliance-вердикт от `compliance-152fz-specialist` (схема размещения данных).
2. Поднять Yandex Cloud: Managed K8s, Cloud SQL Postgres 16, Managed Redis, Container Registry.
3. Настроить Vault / Yandex Lockbox: все secrets вне кода; ротационные политики.
4. GitLab CI пайплайн: build → lint → test → security-scan → docker push → argocd sync.
5. Observability: Grafana + Prometheus + Loki + Tempo + Sentry.
6. Self-audit: `git grep -r "password\|secret\|key" --include="*.yaml" --include="*.env"` → нет совпадений в repo.
7. Handoff → `backend-implementer` (env-переменные) + `crawler-probe-specialist` (сетевая топология).

---

## 2. Dual-geo probe-ноды (P5)

**Trigger.** `planner` выдаёт задачу P5: развёртывание зарубежных нод.

**Steps.**
1. Поднять VPS (Hetzner/Selectel) в нужных геолокациях (EU/US).
2. Изолировать сеть: зарубежные ноды не имеют доступа к RF-данным; только входящий probe-трафик.
3. Настроить proxy rotation (резидентные прокси Smartproxy/Bright Data): credentials в Vault.
4. Verify: сделать test-probe → подтвердить, что исходящий IP не RF (проверка IP-геолокации).
5. Handoff → `crawler-probe-specialist` (endpoint зарубежных нод).

---

## 3. Rate-limit Tier-0 (P7)

**Trigger.** `planner` выдаёт задачу P7: защита no-auth поверхности.

**Steps.**
1. nginx rate_limit_req: per-IP лимиты (burst + rate для Tier-0 endpoint).
2. FastAPI middleware: per-IP token bucket; возврат 429 с `Retry-After`.
3. Мониторинг: Grafana дашборд rate-limit breaches.
4. Self-audit: нагрузочный тест (локальный) → убедиться, что limit срабатывает.
5. Handoff → `backend-implementer` (middleware конфиг).
