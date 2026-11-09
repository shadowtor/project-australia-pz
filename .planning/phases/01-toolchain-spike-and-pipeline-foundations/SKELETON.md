# Walking Skeleton — Project Australia (Phase 1)

**Phase:** 1
**Generated:** 2026-11-09

## Capability Proven End-to-End

Pinned inputs produce one KnoxMap-built cell that is compiled, composed with a hand edit, passed through the validation gates, released atomically, installed, and loaded in a new Project Zomboid 42.21 Stable save. Plan 01-01 lands the thin version of this chain on fixtures (`pa tracer`); plans 01-06 and 01-08 run it against the real pinned tools; plan 01-09 closes the loop in game.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Pipeline tool | Python 3.13 `pa` package (stdlib first; pytest, pyyaml, pillow) | D-11; Windows dev machine; one small package, no extra abstractions |
| Spike generator | KnoxMap 1.8.5.5 run offline as an external pinned black box | D-08; fastest route to a loading B42 cell; replaced in Phase 2 (D-09) |
| Mapping tools | PZ Mapping Tools 43.00B261030 with the patched CLI; 260909 recorded inactive fallback | user decision after research; compat checked in 01-06 |
| Trees | `generated/` (disposable), `config/`, `edits/` (human), `composed/`, `releases/<ver>` + `current.txt` | ARCHITECTURE; BUILD-02/04 |
| Edit model | Hybrid anchors (D-12), human-only `promote` (D-13), orphan report (D-14) | hand work must survive regeneration |
| Release | Stage, gate, `os.replace` into `releases/<ver>`, pointer-file swap, copy-then-rename install | BUILD-04; NTFS-atomic, no admin needed |
| Large data | `data_dir` on D: (default D:/PA), recorded in PINS by path+hash, never committed | F: has ~4.9 GB free |
| Proof of engine unknowns | Human in-game protocol with structured `run.yaml` evidence validated by `pa decision check` | AI cannot run Zomboid (D-01) |
| Directory layout | `pa/`, `tests/`, `config/`, `edits/`, `ledger/`, `spike/`, `PINS.toml` | RESEARCH recommended structure |

## Stack Touched in Phase 1

- [x] Project scaffold (pyproject, venv, lockfile, pytest) — 01-01
- [x] Pins and supply-chain verification — 01-02
- [x] Edit/compose/orphan layer — 01-03
- [x] Validation gates — 01-04
- [x] Release + ledger/attribution — 01-05
- [x] Generator (KnoxMap wrapper) + compile — 01-06, 01-08
- [x] In-game load, measurements, engine proofs — 01-09 to 01-11
- [ ] Decision record — 01-12

## Template items that do not apply

This is a game-mod toolchain: there is no framework, routing, database, auth, UI, or deployment target. "Routing / Database / UI" rows are N/A. The deployment analogue is the install into `%USERPROFILE%\Zomboid\mods` and the in-game load, covered by 01-05 (install) and 01-09 (load).

## Out of Scope (Deferred to Later Slices)

- Own Python generator with pyosmium (Phase 2, D-09) — KnoxMap must not become the production pipeline
- Real city content, multi-cell corridors, spawn UI, loot/zombie zones (Phase 2+)
- Networkx-based graph analysis (Phase 3)
- ODbL legal posture beyond ledger rows and attribution (Phase 5, REL-02)
- Tasmania ferry content (Phase 6; Phase 1 only proves or rules out the mechanic)

## Subsequent Slice Plan

- Phase 2: Melbourne–Geelong pilot on the own generator, scale decision from measured drives
- Phase 3: national road network and regional production
- Phase 4: identity and selective features (uses Phase 1 ramp/basement/ferry verdicts)
- Phase 5: release gate (union compile, drive matrix, licence audit)
- Phase 6: conditional Bass Strait ferry
