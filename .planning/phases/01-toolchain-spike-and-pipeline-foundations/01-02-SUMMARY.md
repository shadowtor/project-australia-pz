---
phase: 01-toolchain-spike-and-pipeline-foundations
plan: 02
subsystem: infra
tags: [pins, supply-chain, sha256, venv-lock, knoxmap, safe-extract]
requires: [01-01]
provides:
  - PINS.toml single source of pinned versions and checksums (game, python, tools, KnoxMap, PBF, venv)
  - pa pins verify/fetch/manifest with fail-closed checks
  - Reviewed hash-locked KnoxMap venv (25 wheels) at D:/PA/vendor/KnoxMap-1.8.5.5/KnoxMap/.venv
affects: [01-06, 01-08, 01-12]
actuals:
  tokens: 30000
  tasks: 3
  commits: 4
plan_head_before: f9005dcadd74069ae02714c566d859f927c242f8
plan_head_after: 0b7bb334ff3898333b6640bfb170cba535761aeb
tech-stack:
  added: []
  patterns: [stream-hash fetch with temp-then-rename, zip-slip-safe extract, tree manifests, wheels-only hash-locked venv, no downloaded code executed]
key-files:
  created: [PINS.toml, config/world.yaml, tests/test_pins.py, tools/make_proxy_tools_wheel.py, ledger/tools.manifest, ledger/knoxmap.manifest, ledger/knoxmap-requirements.txt, ledger/knoxmap-venv.manifest]
  modified: [pa/pins.py]
key-decisions:
  - "Game pinned to Stable 42.22.2 buildid 26486631 from the C: Steam manifest"
  - "proxy_tools (sdist-only) wheel hand-built from hash-verified sdist, user approved"
  - "KnoxMap .venv lives inside the KnoxMap dir (as KnoxMap expects) and is excluded from the tree manifest, locked separately"
requirements-completed: [BUILD-01]
duration: 60min
completed: 2026-11-10
status: complete
---

# Phase 1 Plan 02: PINS and pins tooling Summary

**PINS.toml pins every external input (game 42.22.2, tools 261030, KnoxMap 1.8.5.5, CLI, PBF with own SHA-256, Python lock) and `pa pins verify` fails closed on drift, including KnoxMap's hash-locked 25-wheel venv.**

## Accomplishments
- `pa/pins.py`: verify (files, externals, trees, appmanifest buildid/BetaKey, python and lock, tools switch rules, venv lock), fetch, safe_extract, tree manifest, `venv_cmd` (`-I -B`); 45 tests pass.
- Real downloads in D:/PA (hashes all matched); tools 261030 active, 260909 inactive fallback; silent switch shape fails verify.
- KnoxMap venv built only from `ledger/knoxmap-requirements.txt` with `--require-hashes --only-binary=:all: --no-deps`; plain `pa pins verify` passes (12 items).

## Task Commits
1. Task 1: `812ce9d` (feat)  2. Task 2: `61aa804` (chore)  3. Task 3: draft `8956e49`, lock `0b7bb33`

## Deviations from Plan
1. **[Orchestrator override] Game 42.22.2 / C: manifest** instead of 42.21 / D:; `recheck_42_22` recorded as done.
2. **[Rule 3] proxy_tools is sdist-only**, so pywebview could not install wheels-only. User chose a hand-built wheel: `tools/make_proxy_tools_wheel.py` extracts the single `__init__.py` from the sdist (sha256 ccb3751f...a28010, never executed) into a deterministic pure wheel (sha256 58255ab0...d4f6). Recorded in PINS `[knoxmap_venv]`.
3. **[Rule 2] Hardening added:** `.venv` tree exclude, verify fails on sourceless `.pyc` outside `__pycache__`, `venv_cmd` forces `-I -B`, venv created `--without-pip` so the installed set equals the reviewed list.
4. Extra `ledger/knoxmap.manifest` and `[external]`/`[trees]` schema; fixtures built in tmp_path (no `tests/fixtures/pins/`); tests and code in one commit (no separate RED commit).

## Known limits
- Venv `Scripts/` launchers are not hashed and must not be executed; run only `venv_cmd` python.
- PBF SHA-256 is trust-on-first-use (T-01-05).

## Known Stubs
None.

## Self-Check: PASSED
Files and commits 812ce9d, 61aa804, 8956e49, 0b7bb33 verified; `pytest tests -q` 45 passed; `pa pins verify` OK.
