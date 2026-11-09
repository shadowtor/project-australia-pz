---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 05
subsystem: infra
tags: [release, atomic, licence-ledger, attribution, provenance, odbl]
requires:
  - phase: 01-toolchain-spike-and-pipeline-foundations
    provides: pa CLI auto-registration, pa/edits.py validators, PINS.toml (plans 01-01, 01-02)
provides:
  - Atomic release store (staging, gates, quarantine, releases/<v>, current.txt pointer) and installer
  - "pa release --payload <dir> --version <v> [--root] [--world --gates-config]" single entry from a build payload
  - Licence ledger (licences.yaml, assets.yaml) and pa ledger check/attribute with provenance.json
affects: [01-06, 01-08, 01-09, 01-11, Phase 5 REL-02]
actuals:
  tokens: 17000
  tasks: 2
  commits: 2
  plan_head_before: 1395a79a40912bfd63cb7dc61bba53d253690d9a
  plan_head_after: a18c132f960a1176b9ce04bc9b27be65bfa8a16e
plan_head_before: 1395a79a40912bfd63cb7dc61bba53d253690d9a
plan_head_after: a18c132f960a1176b9ce04bc9b27be65bfa8a16e
commits: 2
tech-stack:
  added: []
  patterns: [stage-then-os.replace promotion, pointer file instead of junction, fail-closed ledger gate]
key-files:
  created: [pa/ledger.py, ledger/licences.yaml, ledger/assets.yaml, tests/test_release.py, tests/test_ledger.py, tests/fixtures/release/payload/]
  modified: [pa/release.py]
key-decisions:
  - "Releases are immutable: build_release refuses an existing version rather than overwriting."
  - "Install swaps via <id>.new then <id>.old because Windows cannot rename over a non-empty directory; a failed copy leaves the installed mod untouched."
  - "pa release treats a missing or broken pa.ledger as an error, never a skip (T-01-14)."
  - "Transformations come from an optional build record JSON; with none supplied, a default list is used and provenance records transformations_source=default."
requirements-completed: [BUILD-04]
status: complete
---

# Phase 1 Plan 05: Atomic release and licence ledger Summary

Failed generate, compile or gate steps now leave `current.txt` and the previous release byte-identical, and a release is refused unless the payload carries its own OSM credit, extract date and transformations.

## What was built

- **pa/release.py**: `build_release(generate, compile_, gates, root, version)` stages, runs gates, then `os.replace` to `releases/<v>` and rewrites `current.txt` through a temp file. Any failure quarantines staging to `staging-failed/<v>`. Version names and `current.txt` content must be a single path component (T-01-12). `install` copies `releases/<current>` into the mods dir atomically. CLI: `pa release`, `pa install`. Optional `--world/--gates-config` runs the palette gate on staging, with config paths confined to the world dir.
- **pa/ledger.py**: `check_licences`, `check_assets`, `check_payload`, `attribute`. `pa ledger attribute` writes `provenance.json` (extract name/date/sha, tool versions from PINS.toml, transformations), an idempotent credit block in `ATTRIBUTION.txt`, and appends the credit to every `map.info` description without removing text.
- **ledger/licences.yaml**: the six required rows (OSM ODbL, worlded CLI GPL-2.0-or-later, PZ Mapping Tools GPL-2.0, KnoxMap MIT, PZ game assets, Knoxify `not_copied` / "not copied, licence unpublished"). **ledger/assets.yaml**: empty, schema in header.

## Verification

Full suite green: 81 passed (53 before this plan). Failure-injection tests hash `current.txt` and `releases/v1` before and after.

## Copy review (slopmonster)

Public wording (ATTRIBUTION block plus map.info credit) scanned with `strip-hidden-chars.mjs` (0 hidden characters) and `deslop.py`: score 4/5. Single finding: the word "transformation(s)". Left as is: the plan, the check and the ODbL attribution requirement all use that term, and no neutral substitute was invented. No facts were added to satisfy the checker.

## Deviations from Plan

None - plan executed as written. Note: T1 shipped with a temporary tolerance for `pa.ledger` being absent (per the plan's "once pa.ledger exists" wording); T2 replaced it with the strict fail-closed gate in the same plan.

## Requirements

BUILD-04 was already marked complete. BUILD-05 stays Pending: the ledger and attribution writer exist and are enforced, but "shown in the mod" needs the in-game check in plan 01-09.

## Known Stubs

None. Defaults noted: with no build record, `DEFAULT_TRANSFORMATIONS` is used (flagged in provenance.json); plan 01-06/01-08 should pass `--build-record`.

## Threat Flags

None beyond the plan's threat model (T-01-12/13/14 mitigated and tested).

## Self-Check: PASSED

Files present (pa/release.py, pa/ledger.py, ledger/*.yaml, tests); commits 6db8fb1 and a18c132 on main.
