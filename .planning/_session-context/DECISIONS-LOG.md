# Autonomy decisions-log

> Append-only. Every agent-owned fork the autonomous runner resolved without asking the founder (ADR-0021 D4). The founder's post-hoc audit trail. Architectural entries also have an ADR (see `ADR-refs`). Written by `scripts/autonomy/log_decision.py`.

### 2026-07-03T17:17:25Z | phase harness | arch | ADR-0021
- Fork: Integrate ORIION autonomous methodology (ADR-037) into WIZOR
- Decision: Port ADR-037 runner + rails onto WIZOR: .claude/autonomy/ (tripwire/evidence/escalation/judge) + scripts/autonomy/ (8 scripts) + /autonomy commands; lean-adapted to 14-role roster, auditor-as-judge, 3 WIZOR-specific tripwire categories
- Rationale: Founder interview 2026-07-03: integrate ORIION autonomy fully, keep lean (ADR-0001). Machine installed OFF, founder-armed. Amends ADR-0017/0018/0009.
- Reversibility: reversible
