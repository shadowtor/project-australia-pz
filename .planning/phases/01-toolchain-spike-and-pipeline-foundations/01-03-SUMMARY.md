---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 03
subsystem: infra
tags: [edits, anchors, compose, orphans, regeneration]
requires: [01-01]
provides:
  - pa/edits.py anchor schema, resolver, orphan report, promote (sole writer of edits/)
  - pa/compose.py composer with precedence generated < masks < hand overlay < locked
affects: [01-05, 01-08]
actuals:
  tokens: 7000
  tasks: 2
  commits: 2
plan_head_before: 1d41453
plan_head_after: f37b57c07c73ad05941b42c0f24b617f4c7bdc4a
key-files:
  created: [pa/edits.py, tests/test_orphans.py, tests/test_regen.py, edits/locks.yaml, edits/features/.gitkeep, edits/overlays/.gitkeep]
  modified: [pa/compose.py]
key-decisions:
  - "Anchor = geometry hash (translation-invariant); ref alone never anchors"
  - "Overlay layers are opaque text hashed raw (A6, no Qt)"
requirements-completed: [BUILD-02]
status: complete
completed: 2026-11-10
---

# Phase 1 Plan 03: Edit-safe model Summary

**Geometry-hash anchors, per-cell overlays with drift check, whole-cell locks, human-only `pa promote`, orphan report with `--strict`, and D-15 regeneration/perturbation tests passing on fixtures.**

## Accomplishments
- `pa/edits.py`: documented SCHEMA dict, validation (yaml.safe_load, payload path-traversal rejected), `resolve` (survived / moved / missing_source / moved_beyond_tolerance / hash_mismatch), `report` (orphans.json, console table, summary line), `promote`.
- `pa/compose.py`: `run()` returns (out, orphans, counts); `compose()` kept signature-compatible with the tracer; legacy flat `edits/*.yaml` still applied. `pa compose [--strict]` and `pa promote` auto-register.
- Tests: 16 passing total (11 new). Perturbation test orphans exactly the two perturbed edits and no other composed cell changes.

## Task Commits
1. T1 anchor schema/resolver/report - `0d2ee78`
2. T2 composer, promote, D-15 tests - `f37b57c`

## Deviations from Plan
- **TDD RED commit skipped:** tests and implementation were committed together per task (tests were run green; not a separate failing commit).
- Perturbation "shift one node" implemented as shifting a whole footprint (a node shift changes the geometry hash and would yield hash_mismatch, not moved_beyond_tolerance).
- tests/fixtures/regen/ not created; fixture generator lives in tests/test_regen.py (tmp_path), so the dir is unneeded.
- Fixture cells are small text grids (not 256x256); anchor distance still uses 256-cell global coords.

## Known Stubs
None. Real KnoxMap output (cell format, OSM ids) is wired in plan 01-08.

## Self-Check: PASSED
Commits 0d2ee78, f37b57c verified; `pytest tests -q` 16 passed.
