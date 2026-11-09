---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 07
subsystem: measurement-and-evidence
tags: [stats, decision, protocol, d-02, fail-closed]
requires: [01-01, 01-02, 01-13]
provides: [pa stats (pa-stats/1), pa decision check, rollup(), spike/protocol.md, spike/templates/run.yaml]
affects: [01-08, 01-09, 01-10, 01-11, 01-12]
tech-stack:
  added: []
  patterns: [single owner of verdict line format and rollup, yaml.safe_load only, edits.inside path confinement]
key-files:
  created: [pa/stats.py, pa/decision.py, spike/protocol.md, spike/templates/run.yaml, tests/test_stats.py, tests/test_decision_record.py]
  modified: []
decisions:
  - "MB in pa-stats/1 means MiB; per-cell size sums lotpack + lotheader + chunkdata; a cell exists if its lotpack does"
  - "empty_threshold_bytes comes from config/world.yaml or --empty-threshold-bytes; no default is invented, the command exits if neither is set"
  - "Required trial directions (D-03) fixed in decision.REQUIRED_DIRS: ramp up/down, basement in/out, ferry round_trip per group; PROVEN needs 3 passes in each"
  - "RULED OUT 'failed the same way' = same failing directions and same reload outcome across two attempts with different implementation and non-empty logged_cause"
  - "verdict.md may understate (INCONCLUSIVE) but never claim PROVEN/RULED OUT beyond evidence; decision.md must equal the recomputed value and verdict.md"
  - "decision.md waiver covers measurement keys only (not cell_format)"
metrics:
  duration: ~25min
  completed: 2026-11-10
status: complete
actuals:
  tokens: 14000
  tasks: 2
  commits: 2
plan_head_before: 193730bd5e6625b16d53ea02a7b14fca314f7e08
plan_head_after: 30fd3a1ada9cfe2c51697f48b2387dd0c63ee326
commits: 2
---

# Phase 1 Plan 07: Measurement, Evidence Checker and Protocol Summary

`pa stats` emits exactly the `pa-stats/1` keys, `pa decision check` mechanically enforces the D-01/D-02 verdict rules per trial group with one shared rollup, and `spike/protocol.md` plus `spike/templates/run.yaml` give the human sessions (01-09 to 01-11) a fixed format for 42.22.2 Stable.

## Commits
- 9cb99bf feat(01-07): pa stats cell size statistics (pa-stats/1) (4 tests)
- 30fd3a1 feat(01-07): evidence/decision checker, manual protocol and run template (16 tests)

Full suite: 122 passing (102 before).

## Deviations from Plan
- Tests build evidence trees in `tmp_path` via helpers, so `tests/fixtures/decision/` was not created.
- RED runs were not committed separately; tests and implementation landed in one commit per task.
- `config/world.yaml` was not edited. `empty_threshold_bytes` is read from it when present, otherwise via CLI flag. Whoever records the threshold (01-09) should add it to the config.
- Protocol says build 42.22.2 Stable (the plan text and D-04 say 42.21, superseded by `spike/game-build.yaml`).

## Requirements
PILOT-05 and PILOT-06 stay Pending: they need the human in-game sessions of 01-09 to 01-11. This plan supplies only the tooling.

## Known Stubs
None.

## Threat Flags
None. T-01-15 mitigated (D-02 checks, screenshot presence confined with `edits.inside`), T-01-16 mitigated (`yaml.safe_load` only).

## Self-Check: PASSED
