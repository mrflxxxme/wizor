# Autonomy decisions-log

> Append-only. Every agent-owned fork the autonomous runner resolved without asking the founder (ADR-0021 D4). The founder's post-hoc audit trail. Architectural entries also have an ADR (see `ADR-refs`). Written by `scripts/autonomy/log_decision.py`.

### 2026-07-03T17:17:25Z | phase harness | arch | ADR-0021
- Fork: Integrate ORIION autonomous methodology (ADR-037) into WIZOR
- Decision: Port ADR-037 runner + rails onto WIZOR: .claude/autonomy/ (tripwire/evidence/escalation/judge) + scripts/autonomy/ (8 scripts) + /autonomy commands; lean-adapted to 14-role roster, auditor-as-judge, 3 WIZOR-specific tripwire categories
- Rationale: Founder interview 2026-07-03: integrate ORIION autonomy fully, keep lean (ADR-0001). Machine installed OFF, founder-armed. Amends ADR-0017/0018/0009.
- Reversibility: reversible

### 2026-07-05T12:59:37Z | phase P2 | arch
- Fork: Read-only enforcement mechanism (§6 invariant 1)
- Decision: Hard GET-only guard in the crawler HTTP client: any non-GET to an external/client domain raises + appends to audit-log; test AC-7 asserts zero PUT/POST/DELETE to client site
- Rationale: Read-only border is a standing invariant (charter §6.1), not a convention — enforce structurally, not by discipline. Design owned per escalation-policy D4; high blast radius so logged as arch precedent for P6/P8 re-crawl.
- Reversibility: reversible

### 2026-07-05T12:59:37Z | phase P2 | arch
- Fork: Page snapshot storage shape (wide fork)
- Decision: Store extracted structural signals + per-page content-hash, NOT full HTML blobs; full snapshot only behind an explicit flag
- Rationale: Sufficient for P8 re-crawl delta (hash detects change; targeted re-extract confirms), cheaper storage, avoids storing incidental PDn. Wide arch fork, high blast radius (sets crawler.owns data shape) — owned+logged per D4/D5.
- Reversibility: reversible
