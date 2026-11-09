# Phase 1: Toolchain Spike and Pipeline Foundations - Context

**Gathered:** 2026-11-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Pin a reproducible build, settle engine unknowns with evidence (cell format 256 vs 300, ramps, basement entrance, ferry-style teleport), and stand up the edit-safe pipeline (separate trees, validation gates, atomic release, provenance ledger). No city content is scaled in this phase. Requirements: BUILD-01..05, PILOT-05, PILOT-06.

</domain>

<decisions>
## Implementation Decisions

### Engine-proof bar (PILOT-06)
- **D-01:** Tiered proof for ramps/overpass, basement entrance and ferry-style teleport. Each feature needs 3 consecutive passes in one session, then one save / quit-to-menu / reload where it must still work. The user plays and reports; the AI cannot run Zomboid.
- **D-02:** Verdicts: PROVEN only if every required trial passes (one failure = INCONCLUSIVE). RULED OUT only after two independent attempts with different implementations fail the same way, with a logged cause (console.txt or visible symptom) and a plausible engine-level reason.
- **D-03:** Per-trial protocol. Ramp: drive both directions, 3x each, park mid-structure, save/reload, drive off. Basement: walk in/out 3x, reload while inside and outside. Ferry: A→B→A 3x on foot and with a vehicle, save at B, reload, return; no duplicated/vanished zombies or items.
- **D-04:** Evidence per feature in `.planning` checklist and the Phase 1 decision file: build 42.21, mod version, date, per-trial pass/fail, reload result, console errors, one screenshot per result, verdict line (PROVEN / RULED OUT / INCONCLUSIVE + next step).

### Budgets and target machine (PILOT-05, BUILD-03)
- **D-05:** The developer's Windows 11 Pro machine is the single reference machine; record CPU, GPU, RAM, SSD. A minimum-spec note is a later sanity check, not a Phase 1 gate.
- **D-06:** Measure first, then freeze. Record vanilla Muldraugh (and Real USA if installed) on the same machine for MB per populated/empty cell, new-save load time and driving FPS/stream-in; 3 runs, median. Then measure the pilot cell.
- **D-07:** Freeze budgets at spike end as ceilings relative to vanilla into one budgets file read by the BUILD-03 gates. Starting guess: pilot MB/cell no more than ~1.5x vanilla (unconfirmed, to be confirmed with user when frozen); fixed load-time ceiling. Export-size ceiling = cell count x MB/cell (populated vs empty) at the recorded cell format. Re-derive if build or cell format changes. — **Reversibility:** reversible — a config file.

### Spike toolchain (BUILD-01, BUILD-05)
- **D-08:** KnoxMap is used first to get a loading B42 cell fast. Pin its release tag and the patched `PZWorldEd_cli.exe` SHA-256 in PINS, `auto_update` off, Geofabrik extract pinned and checksummed (no Overpass/live pull). Phase 1 proves repeat builds through this pinned KnoxMap path. — **Reversibility:** costly — KnoxMap authors in 300-tile cells and its output conventions may shape the cell-size decision and early config.
- **D-09:** An own Python generator (pyosmium on the pinned extract, PZ Mapping Tools 43.00B261030) is built in Phase 2, replacing KnoxMap before corridor work. Do not let KnoxMap become the production pipeline.
- **D-10:** Licence handling: never copy Knoxify-derived files (no licence published, all rights reserved per KnoxMap LICENSES.md). KnoxMap's patched `worlded/` and prebuilt CLI are GPL-2.0-or-later; run unmodified as an external tool, and ship source if ever redistributed. The BUILD-05 ledger gets rows for ODbL (OSM), GPL-2.0+ CLI, and "not copied, licence unpublished" for Knoxify.
- **D-11:** PINS locks: PZ 42.21 Stable (recheck 42.22 before final pin), PZ Mapping Tools zip + SHA-256, KnoxMap release tag + CLI hash + LICENSES.md hash, Python 3.13 + lockfile (for tooling), Geofabrik extract URL/date/SHA-256, generator commit when it exists.

### Hand-edit overlay and regeneration test (BUILD-02)
- **D-12:** Hybrid model following planned precedence (generated < masks < hand TMX < locked). Discrete features (buildings, landmarks, junctions, stops, road curation) anchor to stable IDs (OSM way/node id or deterministic generated ID + geometry hash + tile offset) in `edits/features/*.yaml`. Freeform painting goes in per-cell overlay TMX layers with a drift check. Whole-cell lock via `locks.yaml` is the escape hatch for heavily hand-built cells. — **Reversibility:** costly — anchor schema is referenced by every later edit and the composer.
- **D-13:** Edits enter `edits/` only through an explicit human `promote` command, which records cell, layers touched, resolved anchors and a hash of the generated tiles overlaid.
- **D-14:** Orphans are never silently dropped or placed: kept in `edits/`, excluded from composed output until re-anchored. Report is `orphans.json` plus console table (`edit_id`, `kind`, `anchor`, `reason` = missing_source | moved_beyond_tolerance | hash_mismatch, last-known cell/tile, file), summary `N edits: X survived, Y moved within tolerance, Z orphaned`; non-zero exit with `--strict`.
- **D-15:** Regen test: snapshot `edits/` hashes, delete `generated/`, regenerate, compose, assert every edit present and `edits/` hashes unchanged; then perturb inputs (remove one way, shift one node past tolerance) and assert exactly those edits orphan and nothing else changes.

### Claude's Discretion
- Validation gate output format and CLI shape (must name region and cell on failure), atomic `releases/<ver>` + `current` swap mechanics, repo layout, in-mod attribution display, and the cell-size decision procedure (compile one cell at 256, keep size a config parameter).
- Note for planner: because KnoxMap is the Phase 1 generator, feature-ID anchoring (D-12) must be proven against whatever IDs KnoxMap output exposes; if it exposes none, anchor via geometry hash + tile offset for the spike and revisit when the own generator lands.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and requirements
- `.planning/PROJECT.md` — constraints, key decisions, licensing posture
- `.planning/REQUIREMENTS.md` — BUILD-01..05, PILOT-05, PILOT-06
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria
- `.planning/STATE.md` — open blockers (ramps, ferry transfer, Knoxify/ODbL licence)

### Research
- `.planning/research/SUMMARY.md` — recommended pins, gaps (256 vs 300, spawnpoints format, standalone map without `lots=`)
- `.planning/research/STACK.md` — toolchain versions and pin rationale
- `.planning/research/ARCHITECTURE.md` — layered build, `generated/` vs `edits/`, composer precedence, atomic release
- `.planning/research/PITFALLS.md` — version drift, seams, budgets, ferry risks

### External
- https://github.com/Unjammer/PZ_Mapping_Tools — toolchain (GPL-2.0)
- https://github.com/spytheeuclidean-a11y/knoxmap — LICENSES.md and README govern reuse
- https://github.com/arytek/knoxify — no LICENSE file; treat as unlicensed
- https://download.geofabrik.de/australia-oceania/ — pinned OSM extract source

</canonical_refs>

<code_context>
## Existing Code Insights

No source code exists yet (planning-only repository). Greenfield; no reusable assets or established patterns. `PROJECT-AUSTRALIA-GSD-BRIEF.md` (untracked) is the original brief.

### Integration Points
- Pinned PZ install on the developer's Windows 11 machine; KnoxMap external tool; PZ Mapping Tools.

</code_context>

<specifics>
## Specific Ideas

- Vanilla Muldraugh (and Real USA if installed) are the measurement baselines for budgets.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-Toolchain Spike and Pipeline Foundations*
*Context gathered: 2026-11-09*
