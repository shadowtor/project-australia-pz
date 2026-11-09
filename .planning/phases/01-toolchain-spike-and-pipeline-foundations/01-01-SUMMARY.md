---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 01
subsystem: infra
tags: [python, pytest, pillow, pyyaml, tracer, atomic-release, steam]
requires: []
provides:
  - spike/game-build.yaml recording Stable 42.22.2 (buildid 26486631)
  - .venv + requirements.lock (pytest 9.2.0, PyYAML 6.0.3, pillow 12.3.0)
  - pa package skeleton with auto-registering CLI and `pa tracer` slice
affects: [01-02, 01-06, 01-09, all later plans]
actuals:
  tokens: 5500
  tasks: 3
  commits: 4
plan_head_before: 57523274d0757071c28bc91283540a105160ea5c
plan_head_after: ffecb6820f05d5ec931e3f03214922267b84c682
tech-stack:
  added: [pytest 9.2.0, PyYAML 6.0.3, pillow 12.3.0]
  patterns: [tracer-first slice, fail-closed pins, staging + os.replace atomic release, importlib auto-registration]
key-files:
  created: [spike/game-build.yaml, pyproject.toml, requirements.lock, .gitignore, pa/__init__.py, pa/__main__.py, pa/cli.py, pa/pins.py, pa/compose.py, pa/gates.py, pa/release.py, tests/test_tracer.py]
  modified: []
key-decisions:
  - "Pin game to Stable 42.22.2 (user decision, D-11 stop resolved)"
  - "Gate findings one per (cell, colour) at first offending pixel"
requirements-completed: [BUILD-01, BUILD-02, BUILD-03, BUILD-04]
duration: 25min
completed: 2026-11-10
status: complete
---

# Phase 1 Plan 01: Toolchain spike and pipeline foundations Summary

**Game pinned to Stable 42.22.2 (buildid 26486631), approved pinned Python venv, and a passing `pa tracer` slice (pins verify, compose with edit, palette gate, atomic release) on fixtures.**

## Accomplishments
- spike/game-build.yaml: branch stable, version 42.22.2, buildid 26486631, SSD WD_BLACK SN850X 2000GB.
- venv with exactly the three human-approved packages (plus their pytest transitive deps, all in requirements.lock).
- `pa tracer` runs pins, copy-generated stand-in, compose, palette gate, atomic release; failure at pins or gate leaves no current.txt. 5 tests pass (4 planned plus a no-`yaml.load` grep for T-01-02).

## Task Commits
1. Task 1: game build record - `cdb5572` (chore)
2. Task 2: venv lock, pyproject, gitignore - `0914be8` (chore)
3. Task 3 RED: failing tracer tests - `78c586e` (test)
4. Task 3 GREEN: pa tracer slice - `ffecb68` (feat)

## Decisions Made
- Stable 42.22.2 is the pin (user decision after seeing the in-game string).
- Hashes in PINS.toml `[files]` are relative to PINS.toml's directory.

## Deviations from Plan

**1. [Checkpoint outcome] Version and install location differ from the plan**
- Plan assumed Stable 42.21 and a D:\SteamLibrary install. Actual: Stable **42.22.2**, installed at `C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid`; manifest `C:\Program Files (x86)\Steam\steamapps\appmanifest_108600.acf` (buildid 26486631, no BetaKey). The D: manifest is a stale unstable-beta copy and was ignored. manifest_path in game-build.yaml is the C: path.
- **Later plans (01-02 PINS.toml, 01-06 compat task) must use 42.22.2, not 42.21.**

**2. [Rule 1 - Bug] YAML parsed `0_0` as an int**
- Found during Task 3 GREEN: unquoted `cell: 0_0` loads as integer 0 under YAML 1.1. Fixture now quotes it (`'0_0'`). Edit files for real cells must quote cell ids; plan 01-0x edits tooling should enforce this.
- Committed in `ffecb68`.

**Total deviations:** 2 (1 plan-assumption change from checkpoint, 1 auto-fix). No scope creep.

## Issues Encountered
- Test 3's "no release" assertion also covers an empty releases dir. Python 3.13.14 used (user Node-LTS note not relevant here).

## User Setup Required
None remaining (Steam beta switched by user).

## Known Stubs
- `pa/cli.py` tracer copies fixture `generated/` as a stand-in for KnoxMap generation; intentional, replaced by plan 06.

## Next Phase Readiness
Plan 01-02 can write PINS.toml with game 42.22.2 / buildid 26486631. Later plans add subcommands via `pa/<name>.py` `register(subparsers)` with no cli.py edits.

## Self-Check: PASSED
Files and commits cdb5572, 0914be8, 78c586e, ffecb68 verified; `pytest tests -q` 5 passed.

---
*Phase: 01-toolchain-spike-and-pipeline-foundations*
*Completed: 2026-11-10*
