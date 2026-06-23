<!-- HEAD-SUMMARY (≤500т): Branch-per-phase, Conventional Commits, тир-таблица (1–5 — задаёт строгость CI/аудита), авто-мердж внутри фазы (CI+reviewer+auditor), human-ревью только на гейте фазы (ADR-0017), exit-ritual, лимит PR < 500 строк. -->

# 05-PR-WORKFLOW — Git / PR / CI-протокол

## Ветки и коммиты

**Ветка на фазу:**
```
phase/P02-crawler-audit
phase/P09-auth-billing
```

**Conventional Commits** с футером:
```
feat(crawler): add async crawl endpoint

Implements FR-1.1: crawl target URL, extract page structure.
Refs: P2, ADR-0008
```

Типы: `feat` / `fix` / `refactor` / `test` / `docs` / `chore`.  
Коммиты — атомарные: один коммит = одно логически завершённое изменение.  
**Лимит PR: < 500 строк diff** (исключение — auto-generated, обсуждается с founder).

## Тир-таблица (charter §2, ADR-0009 → amended by ADR-0017)

Tier задаёт **глубину аудита и строгость CI**, НЕ маршрутизацию на человека. Внутри фазы все tier'ы авто-мерджятся на (зелёный CI + `reviewer` APPROVE + `auditor` PASS). Человек — на **гейте фазы**.

| Tier | Примеры | Аудит (шаг 7) | CI |
|---|---|---|---|
| **1** | Docs, форматирование, dep-patch | 1 линза | Базовый |
| **2** | Тесты, рефактор, copy | 1 линза | Полный |
| **3** | Новый endpoint, компонент, фича | 3 линзы | Полный |
| **4** | Архитектура, security, биллинг, ПДн, auto-fix | 5 линз | Полный + security |
| **5** | Hotfix prod | 1–3 линзы | Критический минимум |

**ИИ-агенты мерджат PR внутри фазы автономно** (ADR-0017): CI green + `reviewer` APPROVE + `auditor` PASS. Человек подключается только на гейте фазы (`founder_signature`). Необратимые внешние действия (реальный prod / деньги / DPA) — отдельный product-runtime consent (ADR-0015).

## Pre-PR gate: тесты + live-gold (ADR-0018)

Перед поднятием PR `verifier` (шаг 6) обязан дать зелёный:
- unit + integration зелёные + coverage-гейт;
- **live-gold, где возможно** — end-to-end против РЕАЛЬНЫХ сервисов с golden-набором; невозможно → явный `deferred_live_gold` в гейте (reason/what/founder_action), НЕ тихий пропуск;
- evidence: `_session-context/VERIFY-<phase>-<ts>.md` (секции `## Tests`, `## Live-gold`).

**PR не поднимается, пока verify не зелёный.** Авто-мердж = CI + `reviewer` + `auditor` + verify.

## CI-гейты (обязательны для всех tier)

```
lint          → ruff (Python) + eslint (JS/TS)
type-check    → mypy --strict + tsc --strict
unit-tests    → pytest; coverage ≥ 70% новый код / ≥ 85% security-critical
security      → semgrep + bandit + gitleaks + pip-audit + npm audit
migrations    → squawk (safety check)
secrets       → gitleaks (нет секретов в диффе)
```

Для tier 4 дополнительно:
```
container     → Trivy scan
sbom          → Syft + Grype
license       → нет GPL/AGPL
```

## Exit-ritual (обязателен перед merge)

Выполняет `memory-curator` на шаге 8 цикла фазы:

1. **JOURNAL +1** — дописать запись в `.planning/JOURNAL.md` (append-only)
2. **HANDOFF refresh** — перезаписать снапшот `.planning/HANDOFF.md` (≤ 2 KB)
3. **README status-block regen** — обновить статус-блок в `README.md`
4. Упомянуть оба обновления в **описании PR**

Без exit-ritual review-gate блокирует мердж.

## Описание PR

```markdown
## Summary
- <что сделано, 1–3 буллита>
- Phase: PNN-slug | Tier: N | ADR: ADR-NNNN (если tier 4)

## Acceptance criteria
- [ ] AC1 из phase-spec
- [ ] AC2 из phase-spec

## Exit-ritual
- [ ] JOURNAL.md дополнен
- [ ] HANDOFF.md обновлён
- [ ] README статус-блок регенерирован

## Audit
Вердикт: PASS | PASS-WITH-FIXES  
Отчёт: _session-context/AUDIT-YYYY-MM-DD-PNN/AUDIT-REPORT.md
```

## Anti-patterns

- **Коммит «fix everything»** — разбивай на атомарные.
- **PR > 500 строк** — сплитти или обсуди с founder.
- **Ждать founder-аппрув на каждый PR** — внутри фазы мердж автономен; человек только на гейте (ADR-0017).
- **Секреты в коде** — gitleaks поймает; но лучше не пускать.
- **Skip exit-ritual** — следующая сессия стартует вслепую.
