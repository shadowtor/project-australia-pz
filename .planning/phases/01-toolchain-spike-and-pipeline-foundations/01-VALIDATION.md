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
| 01-02-T1, 01-02-T2 | 02 | 2 | BUILD-01 | tool supply chain | every downloaded tool hash-verified against PINS | unit + integration | `pytest tests/test_pins.py`; `pa pins verify` | ❌ W0 | ⬜ pending |
| 01-06-T1, 01-08-T1 | 06, 08 | 3, 4 | BUILD-01 | offline build, no live pull | proxy-poisoned repeat build, identical manifests | unit + integration | `pytest tests/test_build_wrapper.py`; `pa build --check-repeat` | ❌ W0 | ⬜ pending |
| 01-03-T1, 01-03-T2, 01-08-T2 | 03, 08 | 2, 4 | BUILD-02 | edits never overwritten; orphans reported | regen + perturbation | unit + integration | `pytest tests/test_regen.py tests/test_orphans.py` | ❌ W0 | ⬜ pending |
| 01-04-T1, 01-04-T2, 01-08-T2 | 04, 08 | 2, 4 | BUILD-03 | gates fail naming region and cell | broken-world fixtures | unit + integration | `pytest tests/test_gates.py` | ❌ W0 | ⬜ pending |
| 01-05-T1 | 05 | 2 | BUILD-04 | failed build leaves last export intact | failure injection | unit | `pytest tests/test_release.py` | ❌ W0 | ⬜ pending |
| 01-05-T2, 01-09-T2 | 05, 09 | 2, 5 | BUILD-05 | attribution and licence ledger present and visible | ledger check + in-game | unit + manual | `pytest tests/test_ledger.py` | ❌ W0 | ⬜ pending |
| 01-07-T1, 01-07-T2, 01-09-T1..T3, 01-12-T1 | 07, 09, 12 | 2, 5, 6 | PILOT-05 | decision record complete; budgets frozen | stats + manual | unit + manual | `pytest tests/test_stats.py tests/test_decision_record.py`; `pa decision check` | ❌ W0 | ⬜ pending |
| 01-10-T1..T3, 01-11-T1..T3 | 10, 11 | 5 | PILOT-06 | D-02 verdict rules enforced | evidence schema + manual | unit + manual | `pa decision check --feature <f> --evidence spike/evidence` | ❌ W0 | ⬜ pending |
| 01-01-T3 | 01 | 1 | BUILD-01..04 (tracer) | thin end-to-end slice | tracer on fixtures | unit | `pytest tests/test_tracer.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs are filled in by the planner.*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` with pytest config; `.venv` + `requirements.lock`
- [ ] `tests/fixtures/` — tiny BMP cells, `Rules.txt` excerpt, routes fixture, edits fixture
- [ ] `tests/test_pins.py`, `test_regen.py`, `test_orphans.py`, `test_gates.py`, `test_release.py`, `test_ledger.py`, `test_decision_record.py`
- [ ] Fake-KnoxMap stub for wrapper unit tests
- [ ] Human-verify checkpoint before first `pip install` (pytest, pyyaml, pillow flagged SUS by the package seam: too-new / unknown-downloads)

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

**Approval:** pending
