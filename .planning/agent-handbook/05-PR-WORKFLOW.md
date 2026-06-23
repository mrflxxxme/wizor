<!-- HEAD-SUMMARY (≤500т): Branch-per-phase, Conventional Commits, тир-таблица PR (1–5, founder sole human approver tier 3+), CI-гейты, exit-ritual перед мержем, лимит PR < 500 строк. -->

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

## Тир-таблица (charter §2, ADR-0009)

| Tier | Примеры | Founder action | CI |
|---|---|---|---|
| **1** | Docs, форматирование, dep-patch | Auto-merge при зелёном CI | Полный |
| **2** | Тесты, рефактор, copy | Skim + ack | Полный |
| **3** | Новый endpoint, компонент, фича | **Explicit approve** | Полный |
| **4** | Архитектура, security, биллинг, ПДн, auto-fix | **Explicit approve + ADR-ссылка** | Полный + security |
| **5** | Hotfix prod | **Same-session approve** | Критический минимум |

**ИИ-агенты не имеют права мержить tier 3+ PR.** CI green + AI review = необходимо, но не достаточно.

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
- **Мерж без founder approve (tier 3+)** — блокировано политикой.
- **Секреты в коде** — gitleaks поймает; но лучше не пускать.
- **Skip exit-ritual** — следующая сессия стартует вслепую.
