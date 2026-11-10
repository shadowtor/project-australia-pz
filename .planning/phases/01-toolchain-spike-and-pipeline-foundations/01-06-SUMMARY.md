---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 06
subsystem: build
tags: [knoxmap, offline-build, compat-261030, pa-build, prepare-tools]
requires: [01-02]
provides:
  - "pa build: offline KnoxMap driver (pins gate, locked venv python, extract-only, poisoned proxy, loopback server always killed) writing build-record.json and payload/"
  - "pa build --project <pzw> --mod-id <id>: hand-authored compile and package path (for 01-11)"
  - "prepare-tools stage: config-driven tools configuration (tiles, PZTools.ini, Rules.txt patches) with prepare-record.json hashes"
  - "spike/compat-261030.md: PASS-with-caveats verdict for KnoxMap flow vs tools 261030"
affects: [01-08, 01-09, 01-11, 01-12]
actuals:
  tokens: 40000
  tasks: 3
  commits: 5
plan_head_before: 906ad37
plan_head_after: 31cc938
tech-stack:
  added: []
  patterns: [launcher via -c with sys.path insert under -I, fresh work-dir copy of verified trees, process-tree kill on timeout, fake-KnoxMap fixture]
key-files:
  created: [pa/build.py, config/knoxmap.yaml, tests/test_build_wrapper.py, tests/fixtures/fake_knoxmap/, spike/compat-261030.md]
  modified: []
key-decisions:
  - "Tools 261030 stays the active pin (user confirmed PASS-with-caveats); PINS.toml untouched"
  - "KnoxMap runs on a copy of the verified trees under data_dir/work; the vendored trees are never written to"
  - "Standalone is set through KnoxMap's /api/placement route, no UI step (assumption A9 resolved)"
requirements-completed: [BUILD-01]
duration: ~4h (incl. long real builds)
completed: 2026-11-10
status: complete
---

# Phase 1 Plan 06: Offline KnoxMap wrapper and 261030 compat check Summary

**`pa build` drives the pinned KnoxMap offline end to end (generate, knoxbuild, compile, package) under the locked venv python; a real run with tools 261030 compiled 3 of 4 output cells with no Qt/DLL/version errors, and the user confirmed 261030.**

## Accomplishments
- `pa/build.py`: pins verify gate before any subprocess; fresh work dir with copies of the verified KnoxMap and tools trees; offline env (KNOXMAP_PBF_FILE, OSM_SOURCE=extract, NO_DISCORD, proxy http://127.0.0.1:9, auto_update=false); server on 127.0.0.1 always killed; network text in the log fails the build; deterministic BMP/.pzw/.tbx manifest; `build-record.json` plus `payload/` for `pa release`.
- `--cells` override and `--project/--mod-id` hand-authored path; `prepare-tools` stage; compile timeout 300 s, one attempt, process tree killed on timeout.
- 13 tests in `tests/test_build_wrapper.py` against a fake KnoxMap. Full suite 135 passed; `pa pins verify` OK (12 items).
- Real compat run recorded in `spike/compat-261030.md` (result PASS with caveats; in-game load is verified in 01-09).

## Task Commits
1. Task 1 wrapper + tests: `43f7dd8`
2. Task 2 real run and compat note: `48c869a` (first FAIL note), `d734fd8` (prepare-tools + timeout), `03a54e3` (road-rule exit 3), `31cc938` (final PASS note)
3. Task 3 decision: user answered "Continue" (PASS acknowledged, 261030 kept); no PINS change.

`commits: 5` is measured as `git rev-list --count 906ad37..31cc938`; the later b0df6a8 (README/LICENSE) belongs to another agent.

## Run history (work dirs under D:/PA/work)
- run1: generate and knoxbuild fine; compile refused, KnoxMap will not compile basements without knoxlots.
- run2: basements disabled; compile hung 30 min on the tools' modal "Initial Setup" dialog (Tiles not configured). Killed.
- run3: prepare-tools ran (530 of 543 tile sheets); stopped because the road patch script exited 3.
- run4: exit 3 tolerated as a recorded warning; build OK, 3 cells compiled in 127 s.

## Deviations from Plan
1. **[Rule 3 - plan 01-02 gap] prepare-tools stage added.** 01-02 locked the venv but not tools configuration; the CLI needs `PZTools.ini` TilesDirectory, extracted tile sheets and patched Rules.txt, otherwise it blocks on a hidden dialog. User approved ("Yes, with patch"). Runs only KnoxMap's `configure_tools` and the two Rules patch scripts (locked python, `-I -B`, work copy of the tools, game read-only); Setup's downloads and pip are never run. Hashes in `prepare-record.json`.
2. **[Rule 1] Basements disabled** (`basement_share: 0, max_basement_depth: 0`) because only knoxlots (rust, not built) can compile them; handled by hand-authored maps in 01-11 (PILOT-06).
3. **[Rule 1] Road-rule exit 3 tolerated** as a recorded warning: Build 42.22.2 ships `floors_exterior_natural_01_018` blank, KnoxMap drops its "Yard bed_soil" rule and its strict check fails though 264 rules were written.
4. **[Rule 2] Hard compile timeout (300 s), single attempt, tree kill** added at the user's request after the 30-minute hang.
5. Launcher via `-c` with `sys.path` insert because `-I` drops the script directory; compile uses KnoxMap's `compile_map` (not a bare CLI call) so bitmap conversion and batching match KnoxMap.

## Caveats
- Output cell 1,1 did not compile: building `pa_spike_melb_2194.tbx` uses `furniture_shelving_erika_01` (Erika's Tiles mod, not installed). Content issue, not a tools-version one.
- `--check-repeat` has not been run on real data (the .pzw likely embeds the work dir path); covered by the fake only.
- The ~300 m bbox became 600x600 tiles (2x2 source cells; rotated and padded).
- knoxlots not built; bogus `camping_03 (... conflicted copy ...)` catalogue entry exists in both tools versions.

## Known Stubs
None.

## Self-Check: PASSED
Files present (pa/build.py, config/knoxmap.yaml, tests/test_build_wrapper.py, tests/fixtures/fake_knoxmap, spike/compat-261030.md); commits 43f7dd8, 48c869a, d734fd8, 03a54e3, 31cc938 are ancestors of HEAD; `pytest tests -q` 135 passed; `pa pins verify` OK.
