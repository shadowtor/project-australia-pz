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
| 01-xx | TBD | TBD | BUILD-01 | tool supply chain | every downloaded tool hash-verified against PINS | unit + integration | `pytest tests/test_pins.py`; `pa build --check-repeat` | ❌ W0 | ⬜ pending |
| 01-xx | TBD | TBD | BUILD-02 | — | hand edits never overwritten; orphans reported | unit | `pytest tests/test_regen.py tests/test_orphans.py` | ❌ W0 | ⬜ pending |
| 01-xx | TBD | TBD | BUILD-03 | — | gates fail naming region and cell | unit | `pytest tests/test_gates.py` | ❌ W0 | ⬜ pending |
| 01-xx | TBD | TBD | BUILD-04 | — | failed build leaves last export intact | unit | `pytest tests/test_release.py` | ❌ W0 | ⬜ pending |
| 01-xx | TBD | TBD | BUILD-05 | — | attribution and licence ledger present | unit | `pytest tests/test_ledger.py` | ❌ W0 | ⬜ pending |
| 01-xx | TBD | TBD | PILOT-05, PILOT-06 | — | decision record complete, verdict rules enforced | unit + manual | `pytest tests/test_decision_record.py`; `pa stats <map_dir>` | ❌ W0 | ⬜ pending |

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
