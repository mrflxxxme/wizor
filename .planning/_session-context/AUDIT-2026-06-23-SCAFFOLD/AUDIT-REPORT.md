# AUDIT-REPORT — Scaffold v1.0 (post-build, step 7)

**Phase:** Scaffold bootstrap · **Date:** 2026-06-23 · **Auditor:** auditor/Opus (adversarial)
**Scope:** read-only documentation scaffold at `wizor-build` · **Risk-tier:** right-sized single thorough lens (charter §6 — scaffold is docs-only, no prod code)
**Sources of truth:** `.planning/_meta/BUILD-CHARTER.md` (v1.0), `.planning/PRD.md` (v0.2)

---

## Verdict: **PASS-WITH-FIXES**

The scaffold is faithful, internally coherent, and conforms to the charter to an unusually high degree. All structural elements the charter implies are present (8 core + 6 specialist agents fully fleshed; 11 phase-specs P00–P10; 16 ADRs + template + index; 13 contract stubs + map; gates + schema; `_meta`; agent-handbook 00–07; all state/memory files). Phase-spec frontmatter matches the charter §5 roadmap table exactly; PRD FR codes and acceptance criteria are cited verbatim and correctly; all 10 standing invariants are encoded in the auditor checklist and surfaced as testable ACs in the relevant phases.

**6 broken cross-references (one P1 cluster) were fixed in-loop.** The remaining findings are P2/P3 and deferred to the founder — none block the scaffold from serving as the build baseline.

---

## Findings

| ID | Sev | Dimension | Finding | Disposition |
|----|-----|-----------|---------|-------------|
| F-01 | **P1** | Cross-references / Consistency | Gate filename mismatch: actual file is `gates/P0-to-heavy-autofix.md` (matches charter §8.5 example & gate frontmatter `gate: P0-to-heavy-autofix`), but 6 references pointed to non-existent `P00-to-heavy-autofix.md` (double-zero) — 5× in `roadmap/P00-discovery.md` (HEAD-SUMMARY, In-scope, AC-4, exit-gate table, decomposition hint #1) + 1× in `roadmap/P10-auto-track.md` exit-gate table. P10's exit-gate is the literal gate-pass check, so this broke the most load-bearing pointer in the roadmap. | **fixed-in-loop** (6 edits; verified 0 remaining refs, target confirmed to exist) |
| F-02 | **P2** | Consistency | Inconsistent / non-canonical model IDs in agent `profile.md` frontmatter. Core Sonnet agents (backend, frontend, reviewer) use `claude-sonnet-4-5`; the 3 Sonnet *specialists* (crawler-probe, cms-connector, devops-infra) use `claude-sonnet-4-6`; `_shared/cost-budget.yaml` `fallback_model` also uses `claude-sonnet-4-6`. Two different Sonnet version suffixes for the same tier is internally contradictory, and both strings appear to be non-canonical Anthropic model IDs. Role→tier mapping (Opus/Sonnet/Haiku) is correct everywhere vs charter §3, so behavior is unaffected — but the IDs will not resolve if consumed literally. | **deferred** — picking a single canonical model ID is a substantive founder/config decision, not a mechanical edit. Recommend: normalize all Sonnet agents to one ID, all Opus to one, all Haiku to one (or drop pinned IDs and let the harness default per tier). |
| F-03 | **P3** | Consistency / Format | Profile-format drift between the two agent cohorts. The 8 core agents put `triggers / owns / escalates_to` in the *body* (prose); the 6 specialists put them *inside* the YAML frontmatter. Charter §8.1 lists those as profile fields but does not pin frontmatter-vs-body, so neither violates spec — but the inconsistency is visible and slightly raises parsing cost for any tool reading profiles. | **deferred** — cosmetic; founder may standardize on one layout. |
| F-04 | **P3** | Completeness | `.planning/memory.md` does not exist, yet `memory-curator/profile.md` declares `owns: .planning/memory.md` and charter §4 step 8 + §10 reference writing `patterns/pitfalls в memory.md`. `MEMORY-INDEX.md`'s `patterns` row points instead to `.claude/agents/<role>/memory.md` (which all exist). Not a defect for a scaffold — the file is created on first phase memory-update — but the pointer target is currently dangling. | **deferred** — expected to be created at first step-8 run; optionally seed an empty `.planning/memory.md` with a header to make the `owns` pointer resolve immediately. |
| F-05 | **P3** | Cross-references | Gate frontmatter `risks_delta.opened: [R-1, R-2]` (in `P0-to-heavy-autofix.md`) and the schema's `risks_delta` pattern reference `.planning/risks/` (per schema description), but no `risks/` directory or risk-register exists yet. Schema validates (pattern-only, no existence check), so not breaking. | **deferred** — create `.planning/risks/` register when P0 opens, or drop the seeded R-1/R-2 until the register exists. |
| F-06 | P3 | Lean-size discipline | `compliance-152fz-specialist/system-prompt.md` = 4101 bytes, marginally over the 4096-byte (4 KB) line but within the charter's "~4 KB" guidance (§8.1). All other 13 system-prompts are well under. | **deferred** — trim ~5 bytes if a hard 4 KB cap is desired; otherwise acceptable under "~4 KB". |

No P0 findings.

---

## Dimension-by-dimension result

1. **Completeness — PASS.** Every artifact the charter implies is present and counted: 14 agents × (profile/system-prompt/workflows/memory/handoff-templates/tools-allowlist) + checklists; `_shared/` (cost-budget.yaml, handoff-schema.md, 3 pipeline-templates); `AGENTS.md`; 11 phase-specs (P00–P10); `ROADMAP.md`; 16 ADRs (0001–0016) + template + README index; 13 contract stubs + map README; gates (`_schema/gate.schema.json` + `P0-to-heavy-autofix` + `A-to-B`); `_meta` (charter/conventions/stack/glossary/README); agent-handbook 00–07; STATUS/HANDOFF/JOURNAL/MEMORY-INDEX/PROJECT/PHASE-HISTORY/OPEN-QUESTIONS/PLACEHOLDERS. Only gap: `.planning/memory.md` (F-04, bootstrap-created).

2. **Consistency — PASS-WITH-FIXES.** 16 ADRs faithfully encode all 17 charter §2 decisions (the §2 table itself maps #4→ADR-0004 and #11→ADR-0004, #2→ADR-0002 and #5→ADR-0002, so 16 ADRs for 17 decisions is correct by design, plus 4 product ADRs 0013–0016; ADR README's crosswalk is accurate). Phase-spec frontmatter (tier/track/depends_on/gated_by/contracts/specialists/prd_refs) matches charter §5 row-for-row. **P10 `gated_by: [P0]` confirmed** (both frontmatter and exit-gate). P7 `depends_on: [P2,P3,P4,P5,P6]` matches "P2–P6". Model *tiers* in profiles are consistent with charter §3 everywhere; only the literal model-ID *strings* are inconsistent (F-02). Specialist trigger-phase lists (e.g. geo P3/P6/P7/P10, crawler P2/P5/P6/P8) align with the roadmap's specialist column.

3. **PRD fidelity — PASS.** Spot-checked P06/P07/P10 deeply + P02/P03/P05. All cite real FR codes with ACs matching the PRD: P06 carries FR-3.1–3.5 incl. competitive-gap evidence (FR-3.3), copy-paste Manual-track patches (FR-3.4), honest forecast with `visibility_guarantee` absent-from-schema test (FR-3.5); P07 Tier-0 correctly degrades probe to 1 run (not N≥5) with disclaimer and anon-tenant TTL; P10 carries all FR-4.1–4.7 with idempotency/rollback/append-only/DPA-gate/FAQ-never-auto ACs. No invented or mismatched requirements found. PRD-specific corrections (llms.txt repositioning §7.1, three-track §4.1) are correctly propagated.

4. **Invariant coverage — PASS.** All 10 standing invariants (charter §6) are present in `auditor/checklists/invariant-checklist.md` with per-invariant checks and a BLOCKED rule for #1/#3/#9. They are also surfaced as concrete ACs where they must bite: read-only boundary (P02 AC-7, P06 AC-6, P07 AC-3, P10 AC-8), honest-forecast (P06 AC-5), auto-fix safety (P10 AC-4/5/6/7), probe-geo no-RU-IP (P05 AC-2, P04 AC-4), llms.txt-not-scored (P03 AC-2), ПДн-residency (P01 FR-P1-3, P04 compliance review), uncertainty N≥5+CI (P05 AC-3, P08 AC-2/6), multi-tenant (P01 AC-6, P09 AC-2), secrets (conventions + PLACEHOLDERS policy), FAQ-not-auto (P06 AC-2, P10 AC-3). Contract stubs (e.g. `autofix`) reference the relevant invariant numbers.

5. **Cross-references — PASS-WITH-FIXES.** README/CLAUDE.md/`.planning/README.md`/PROJECT.md/MEMORY-INDEX/ADR-README/`_meta/README` internal links all resolve. The only broken links were the gate-filename cluster (F-01, fixed). F-04/F-05 are dangling *declared* pointers (memory.md, risks/) rather than markdown links, deferred.

6. **Lean-size discipline — PASS.** 14/14 system-prompts ≤ ~4 KB (range 2227–4101 bytes); only one is marginally over 4096 (F-06). Agent folders are well within the §8.1 lean budget.

---

## Post-fix verification note

- **F-01 fixes applied and verified:** 6 edits across `P00-discovery.md` (×5) and `P10-auto-track.md` (×1) changing `P00-to-heavy-autofix.md` → `P0-to-heavy-autofix.md`. Re-grep confirms **0** remaining `P00-to-heavy` references; `test -f` confirms the canonical target `gates/P0-to-heavy-autofix.md` exists. No content/semantic change beyond the path correction.
- All fixes are safe mechanical cross-reference corrections (charter-sanctioned in-loop fix class). No substantive/judgment edits were made.
- Invariant checklist status for this audit: all 10 invariants **N/A-but-encoded** (no product code exists to violate them); structural presence verified. No invariant left unencoded → no BLOCKED trigger.

**Remaining founder attention:** F-02 (normalize model IDs — internal inconsistency + likely non-canonical strings) is the only finding worth a deliberate decision before agents are first spawned; F-03/F-04/F-05/F-06 are low-priority polish.
