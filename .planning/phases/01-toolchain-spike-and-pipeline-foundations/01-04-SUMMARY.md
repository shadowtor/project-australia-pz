---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 04
subsystem: validation-gates
tags: [gates, palette, seam, connectivity, budget, fail-closed]
requires: [01-01, 01-02, 01-13]
provides: [pa.gates (palette_gate, seam_gate, connectivity_gate, budget_gate, load_gates_config, `pa validate`), pa.palette.parse_rules, config/gates.yaml]
affects: [01-05, 01-08, 01-09, 01-12]
tech-stack:
  added: []
  patterns: [Finding list per gate, union-find stdlib, budget/stats read only via pa.schema, config-driven regions]
key-files:
  created: [pa/palette.py, config/gates.yaml, tests/test_gates.py]
  modified: [pa/gates.py]
decisions:
  - "Connectivity flags every node outside the largest component (covers isolated nodes and split networks)"
  - "Findings without a cell (schema/IO/config errors) print region=n/a cell=n/a rather than inventing coordinates"
  - "Budget gate also fails on stats vs budgets cell_size mismatch (fail closed)"
metrics:
  duration: ~20min
  completed: 2026-11-10
status: complete
actuals:
  tokens: 9000
  tasks: 2
  commits: 1
plan_head_before: a22f13e344eb6207bdb31935bb261d5c0524e0e1
plan_head_after: 5e4fd23d51a27d323fa00bc8e1c154d9475577e9
commits: 1
---

# Phase 1 Plan 04: Validation Gates Summary

Four BUILD-03 gates (palette, seam, connectivity, budget) plus `pa validate`, each failing on deliberately broken fixtures with region and cell named in stdout and `reports/<gate>.json`, and exiting non-zero.

## What was built
- `pa/palette.py`: runtime Rules.txt parser (`{label: (r,g,b)}`), ignores comments and colourless rules, raises on malformed colour lines. No Knoxify palette (test greps `pa/` for `pz_colors`).
- `pa/gates.py`: `palette_gate`, `seam_gate` (per adjacent cell pair, horizontal and vertical), `connectivity_gate` (stdlib union-find over a routes yaml), `budget_gate` (reads only through `pa.schema`; SchemaError, missing measurement without waive, ceiling/floor/stream-in violations all fail; worst `per_cell` offender named for `mb_per_*`), `validate` subcommand registered via `register(subparsers)`; `pa/cli.py` untouched. Tracer/release callers of `palette_gate(bmp, palette)` remain compatible (defaults `cell_size=300`, region `map`).
- `config/gates.yaml`: `bmp_cell_size`, `road_labels`, `regions` (placeholder pilot region; 01-08 fills real values). Loader rejects missing/unknown keys. Cells outside every range report `region=unmapped`.
- Pillow errors become a gate finding (T-01-10); yaml.safe_load only; `--bmp/--routes` confined to `--world` via `edits.inside`; cell ids validated by `edits.cell_id`.

## Verification
`.venv/Scripts/python -m pytest tests -q`: 102 passed (81 prior + 21 new).

## Deviations from Plan
**1. [Process] Tasks 1 and 2 committed together.** Both tasks edit the same files and were implemented test-first in one pass; a single commit `5e4fd23` covers both rather than two. No functional impact.

Otherwise none; plan executed as written. Added `--rules`, `--bmp`, `--routes`, `--reports` flags to `pa validate` (plan listed a subset) since palette/seam need the Rules.txt path and routes need a location.

## Requirements decision
BUILD-03 marked complete: the plan's success criteria (broken connectivity, seam and palette fixtures each fail naming region and cell; budget gate fails closed) are all proven, and the requirement text is about gates running and reporting. Caveat: the real region map/palette against real BMPs and the frozen budgets file are 01-08/01-09.

## Known limits
- `config/gates.yaml` holds placeholder pilot values until 01-08.
- Budget worst-cell region lookup applies the BMP-cell region ranges to game-grid `per_cell` coordinates; revisit when 01-08/01-09 define the mapping.
- Palette gate is a per-pixel Python loop (ponytail comment in code).

## Self-Check: PASSED
Files exist (pa/palette.py, config/gates.yaml, tests/test_gates.py, pa/gates.py); commit 5e4fd23 is on HEAD; full suite green.
