# Spike protocol: manual in-game trials and measurements

The developer plays, and the tools check the paperwork. Build under test: Project Zomboid 42.22.2 Stable
(`spike/game-build.yaml`). Record the mod version for every run.

## Setup for every session

- Launch the game with `-debug` to get the teleport UI.
- Start a brand-new save for each build and each mod version. Old saves keep their old cells.
- Note the build (42.22.2) and the mod version in `run.yaml` before you start.
- Record the machine once in `spike/game-build.yaml` (CPU, GPU, RAM, SSD). This is the single reference machine (D-05).

## Evidence layout

```
spike/evidence/<feature>/<attempt>/run.yaml     # copy of spike/templates/run.yaml, filled in
spike/evidence/<feature>/<attempt>/s*.png       # one screenshot per result
spike/evidence/<feature>/<attempt>/console.txt  # console.txt excerpt, when errors appear
spike/evidence/<feature>/verdict.md             # one verdict line per group, see below
spike/decision.md                               # Phase 1 decision, checked by `pa decision check --decision`
```

Features: `ramp`, `basement`, `ferry`. Ferry has two groups, `foot` and `vehicle`.

D-04 note: the structured evidence lives under `spike/`. The `.planning` checklist D-04 asks for is the
Evidence Checklist section of `01-VALIDATION.md`, filled in by plan 01-12 Task 3 with links into `spike/evidence`.

## Trial checklists (D-03)

A trial is one pass or fail result with a direction label. PROVEN needs three consecutive passes per required
direction in one session, then one save, quit to menu and reload where the feature still works (D-01).

### Ramp or overpass (directions `up`, `down`)
- [ ] Drive up the ramp 3 times, `direction: up`.
- [ ] Drive down the ramp 3 times, `direction: down`.
- [ ] Park mid-structure (`direction: park`, one trial).
- [ ] Save, quit to menu, reload. Set `reload_result`.
- [ ] Drive off (`direction: drive_off`, one trial).

### Basement entrance (directions `in`, `out`)
- [ ] Walk in 3 times, `direction: in`.
- [ ] Walk out 3 times, `direction: out`.
- [ ] Save and reload while inside (`direction: reload_inside`), then walk out.
- [ ] Save and reload while outside (`direction: reload_outside`), then walk in.
- [ ] Set `reload_result` from the two reloads: pass only if both worked.

### Ferry-style teleport (group `foot`, then group `vehicle`, direction `round_trip`)
- [ ] On foot: A to B to A, 3 times, `group: foot`.
- [ ] With a vehicle: A to B to A, 3 times, `group: vehicle`.
- [ ] Save at B, quit to menu, reload, return to A. Set `reload_result` per group.
- [ ] Check for duplicated or vanished zombies and items. Any sighting is a failed trial.

## Verdicts (D-02)

- PROVEN: every trial in the group passed, three per required direction, and the reload passed.
- INCONCLUSIVE: any failure, or not enough trials yet.
- RULED OUT: two attempts with different `implementation` values failed the group the same way (same
  failing directions, same reload outcome), each with a non-empty `logged_cause` (console.txt line or visible
  symptom plus a plausible engine-level reason).
- Feature verdict rolls up: PROVEN only when every group is PROVEN, RULED OUT only when every group is
  RULED OUT, anything else INCONCLUSIVE.

`verdict.md` has one line per group, nothing else is parsed:

```
verdict_ramp: PROVEN
verdict_basement: INCONCLUSIVE
verdict_foot: PROVEN
verdict_vehicle: INCONCLUSIVE
```

Single-group features use the feature name (`ramp`, `basement`). Ferry uses `foot` and `vehicle`.
`pa decision check --feature <name> --evidence spike/evidence` recomputes each verdict from the run.yaml
files and fails if `verdict.md` claims PROVEN or RULED OUT where the evidence does not support it.

## Measurements (D-06)

Run each measurement 3 times on the reference machine and record the median. Do vanilla Muldraugh first, then
the pilot cell, on the same build, same machine and same settings. Methods below are working assumptions
(research A2 to A4). If you change one, write the change in `notes`.

- Cell size: `pa stats <map_dir> --json <out.json>`. Gives MB per populated and per empty cell and the
  export total, in the `pa-stats/1` format. MB here means MiB.
- Load time: seconds from clicking Start on a new save to a controllable character. Use screen capture
  timestamps or a stopwatch. Store as `load_time_s` (median) with each run in `runs`.
- Driving FPS: read from an external overlay such as the NVIDIA overlay or PresentMon while driving a fixed
  2 minute route. Store the median as `fps_driving`.
- Stream-in: yes or no. `true` means no visible pop-in or hitching on the same fixed 2 minute route.
  Store as `stream_in_ok`.
- Save growth: size of the save folder under `Zomboid/Saves` after N minutes of walking (note N), compared
  with the size at the start. Record it in `notes`.

Fill the in-game keys (`load_time_s`, `fps_driving`, `stream_in_ok`, `runs`, `machine`) by hand in the stats
JSON (`spike/vanilla-baseline.json`, `spike/pilot-measure.json`). `pa stats` never writes them.
