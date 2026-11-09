# Phase 1: Toolchain Spike and Pipeline Foundations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-09
**Phase:** 1-Toolchain Spike and Pipeline Foundations
**Areas discussed:** Engine-proof bar, Budgets and target machine, Spike toolchain, Hand-edit overlay and regen test

---

## Engine-proof bar

| Option | Description | Selected |
|--------|-------------|----------|
| Tiered proof | 3 passes + save/reload, two-attempt rule for ruled out, evidence log | ✓ |
| Single smoke pass | Works once = proven | |

**User's choice:** Tiered proof

---

## Budgets and target machine

| Option | Description | Selected |
|--------|-------------|----------|
| Measure vanilla, then freeze | Baseline vanilla on dev machine, ceilings as ratios | ✓ |
| Fixed numbers up front | Guess thresholds now | |

**User's choice:** Measure vanilla, then freeze

---

## Spike toolchain

| Option | Description | Selected |
|--------|-------------|----------|
| Own Python generator | Clean licence, proves BUILD-01 from day one (recommended) | |
| KnoxMap first, own later | Fastest first cell, pinned | ✓ |
| Hand-author one cell | WorldEd/TileZed only | |

**User's choice:** KnoxMap first, own later
**Notes:** Follow-up: pin KnoxMap in Phase 1 for BUILD-01 and build the own generator in Phase 2 (over building a minimal own generator in Phase 1).

---

## Hand-edit overlay and regen test

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid: IDs + overlays + locks | Stable IDs for features, overlay layers for painting, cell lock escape hatch | ✓ |
| Whole-cell lock only | Simple, no orphan reporting | |
| Cell+tile coordinates | Silent misplacement | |

**User's choice:** Hybrid

---

## Claude's Discretion

Validation gate format, atomic release mechanics, repo layout, in-mod attribution, cell-size decision procedure.

## Deferred Ideas

None.
