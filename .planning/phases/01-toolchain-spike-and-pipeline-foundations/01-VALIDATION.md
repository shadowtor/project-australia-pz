---
phase: "01"
slug: "toolchain-spike-and-pipeline-foundations"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-09"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `01-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.2.0 on Python 3.13 (project `.venv`), Windows |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — none yet, Wave 0 installs |
| **Quick run command** | `.venv\Scripts\python -m pytest tests -x -q` |
| **Full suite command** | `.venv\Scripts\python -m pytest tests -q` plus `pa pins verify` and (slow, real tools) `pa build --check-repeat` |
| **Estimated runtime** | ~30 seconds (unit); repeat-build check several minutes |

Local unit tests only; no deployed test environment applies to a game mod. In-game checks are manual and recorded.

---

## Sampling Rate

- **After every task commit:** Run `.venv\Scripts\python -m pytest tests -x -q`
- **After every plan wave:** Run full pytest plus `pa pins verify`
- **Before `/gsd-verify-work`:** Full suite green, real KnoxMap repeat-build check done, spike evidence complete
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-02-T1, 01-02-T2, 01-02-T3 | 02 | 2 | BUILD-01 | tool supply chain, T-01-SC (KnoxMap venv reviewed + hash-locked) | every downloaded tool and every KnoxMap build-time pip package hash-verified against PINS; approved tools switch has a verifiable representation | unit + integration + human-verify | `pytest tests/test_pins.py`; `pa pins verify` | ❌ W0 | ⬜ pending |
| 01-13-T1 | 13 | 2 | PILOT-05, BUILD-03 | schema drift cannot pass a gate | one pa-stats/1 and pa-budgets/1 schema, unknown/missing keys fail closed | unit | `pytest tests/test_schema.py` | ❌ W0 | ⬜ pending |
| 01-06-T1, 01-06-T2, 01-08-T1 | 06, 08 | 3, 4 | BUILD-01 | offline build, no live pull; locked venv only | proxy-poisoned repeat build, identical manifests, manifest_identical true and network_use none (or user waiver) | unit + integration | `pytest tests/test_build_wrapper.py`; `pa build --check-repeat` | ❌ W0 | ⬜ pending |
| 01-03-T1, 01-03-T2, 01-08-T2 | 03, 08 | 2, 4 | BUILD-02 | edits never overwritten; orphans reported | regen + perturbation | unit + integration | `pytest tests/test_regen.py tests/test_orphans.py` | ❌ W0 | ⬜ pending |
| 01-04-T1, 01-04-T2, 01-08-T2 | 04, 08 | 3, 4 | BUILD-03 | gates fail naming region and cell | broken-world fixtures | unit + integration | `pytest tests/test_gates.py` | ❌ W0 | ⬜ pending |
| 01-05-T1, 01-08-T2 | 05, 08 | 3, 4 | BUILD-04 | failed build leaves last export intact, incl. a real failing compile through `pa build` -> `pa release --payload` | failure injection + real path | unit + integration | `pytest tests/test_release.py`; `pytest tests/test_real_integration.py -m integration` | ❌ W0 | ⬜ pending |
| 01-05-T2, 01-09-T2 | 05, 09 | 3, 5 | BUILD-05 | attribution and licence ledger present and visible | ledger check + in-game | unit + manual | `pytest tests/test_ledger.py` | ❌ W0 | ⬜ pending |
| 01-07-T1, 01-07-T2, 01-09-T1..T3, 01-12-T1 | 07, 09, 12 | 3, 5, 7 | PILOT-05 | decision record complete (format, count, size, load time, FPS, stream-in); budgets frozen for every dimension | stats + manual | unit + manual | `pytest tests/test_stats.py tests/test_decision_record.py`; `pa decision check`; `pa validate --budgets --stats` | ❌ W0 | ⬜ pending |
| 01-10-T1..T3 | 10 | 6 | PILOT-06 | D-02 verdict rules enforced per group (ferry foot, vehicle) | evidence schema + manual | unit + manual | `pa decision check --feature ferry --evidence spike/evidence` | ❌ W0 | ⬜ pending |
| 01-11-T1..T3 | 11 | 7 | PILOT-06 | D-02 verdict rules enforced (ramp, basement) | evidence schema + manual | unit + manual | `pa decision check --feature <f> --evidence spike/evidence` | ❌ W0 | ⬜ pending |
| 01-01-T3 | 01 | 1 | BUILD-01..04 (tracer) | thin end-to-end slice | tracer on fixtures | unit | `pytest tests/test_tracer.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs are filled in by the planner.*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` with pytest config; `.venv` + `requirements.lock`
- [ ] `tests/fixtures/` — tiny BMP cells, `Rules.txt` excerpt, routes fixture, edits fixture
- [ ] `tests/test_pins.py`, `test_schema.py`, `test_regen.py`, `test_orphans.py`, `test_gates.py`, `test_release.py`, `test_ledger.py`, `test_stats.py`, `test_decision_record.py`, `test_build_wrapper.py`
- [ ] Fake-KnoxMap stub for wrapper unit tests
- [ ] Human-verify checkpoint before first `pip install` (pytest, pyyaml, pillow flagged SUS by the package seam: too-new / unknown-downloads) - 01-01-T2
- [ ] Human-verify checkpoint before building KnoxMap's venv (every package KnoxMap executes, wheels only, hash-locked) - 01-02-T3

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Steam install on Stable (not `unstable` beta), buildid recorded in PINS | BUILD-01 | Steam client action | User switches beta off, updates, run game once |
| New save loads pilot cell standalone; spawn works | PILOT-05 | AI cannot run Zomboid | Follow `spike/protocol.md` |
| Ramp / basement / ferry teleport trials with save/reload | PILOT-06 | AI cannot run Zomboid | 3 passes + save/quit/reload per D-01..D-04; log to `spike/evidence/` |
| Vanilla baseline: load time, FPS, stream-in (3 runs, median) | PILOT-05 | In-game measurement | Re-measure after update to Stable |
| Attribution visible in mod | BUILD-05 | In-game UI | Check mod description / ATTRIBUTION file in game |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

## Evidence Checklist (D-04, filled by plan 01-12 Task 3)

One row per feature/group (ramp, basement, ferry foot, ferry vehicle) linking into `spike/evidence/<feature>/`: build, mod version, date, per-trial result, reload result, console errors, screenshot, verdict line. Empty until 01-12.

**Approval:** pending
