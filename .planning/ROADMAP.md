# Roadmap: Project Australia

## Overview

Build a Project Zomboid Build 42 map of twelve Australian city districts joined by one physical, driveable highway network. Risky engine unknowns (cell format, ramps, seams, budgets) are proven first on a Melbourne-Geelong pilot. Then the network scales region by region, identity features are added, and a release gate validates everything. Tasmania is a separate conditional phase that never blocks the mainland.

## Phases

- [ ] **Phase 1: Toolchain Spike and Pipeline Foundations** - Pin the build, prove engine unknowns, stand up validation gates and the edit-safe pipeline
- [ ] **Phase 2: Melbourne-Geelong Pilot** - A playable two-district slice joined by a compressed Princes Freeway, used to choose scale
- [ ] **Phase 3: National Road Network and Regional Production** - All twelve destinations on one continuous signed highway network
- [ ] **Phase 4: Identity and Selective Features** - Landmarks, biomes, proven multi-level features, roadside events, found maps
- [ ] **Phase 5: Release Gate** - Union compile, full drive matrix, licence audit, clean-install acceptance
- [ ] **Phase 6: Bass Strait Ferry (Conditional)** - Tasmania only if the ferry passes its own gate

## Phase Details

### Phase 1: Toolchain Spike and Pipeline Foundations

**Goal**: A pinned, reproducible build exists, engine unknowns are settled with evidence, and the pipeline protects hand work and reports failures before any content is scaled.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-04, BUILD-05, PILOT-05, PILOT-06
**Success Criteria** (what must be TRUE):
  1. A build repeats from the PINS file (game build, tools, generator revision, OSM extract with checksums) with no live data pull.
  2. A regeneration test shows a hand edit survives and an orphaned edit is reported.
  3. Deliberately breaking connectivity, a seam road or a palette tile makes a validation gate fail and name the region and cell.
  4. A deliberately failed generation or compile leaves the last playable export installed and loadable.
  5. A recorded decision shows cell format (256 vs 300), MB per populated/empty cell, new-save load time, and proven-or-ruled-out results for ramps, basement entrance and ferry-style teleport with save/reload.

**Plans**: 8/13 plans executed
Plans:
- [x] 01-01-PLAN.md — Steam Stable switch, pip legitimacy check, `pa tracer` walking skeleton
- [x] 01-02-PLAN.md — PINS.toml, hash verify/fetch, safe extract, reviewed hash-locked KnoxMap venv
- [x] 01-03-PLAN.md — Anchors, promote, composer, orphans, regen test
- [x] 01-04-PLAN.md — Connectivity, seam, palette, budget gates
- [x] 01-05-PLAN.md — Atomic release, install, licence ledger and attribution
- [x] 01-06-PLAN.md — Offline KnoxMap wrapper and 261030 compatibility check
- [x] 01-07-PLAN.md — Stats, evidence/decision validator, in-game protocol
- [ ] 01-08-PLAN.md — Real repeat build, output inspection, real-output tests, 256 vs 300 compare
- [ ] 01-09-PLAN.md — Vanilla/pilot in-game baselines, attribution check, frozen budgets
- [ ] 01-10-PLAN.md — Ferry-style teleport spike mod and trials
- [ ] 01-11-PLAN.md — Ramp and basement feasibility and trials
- [ ] 01-12-PLAN.md — Decision record, 42.22 recheck, phase gate
- [x] 01-13-PLAN.md — Shared stats/budgets schema (pa-stats/1, pa-budgets/1)

### Phase 2: Melbourne-Geelong Pilot

**Goal**: A player can spawn in Melbourne or Geelong, loot, find a car and drive the Princes Freeway between them, and the scale choice is made from measured drives.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: PILOT-01, PILOT-02, PILOT-03, PILOT-04, SCALE-01, BUILD-06
**Success Criteria** (what must be TRUE):
  1. From a clean install, following documented steps with no companion mod, a new save starts at either of two supported spawns (one Melbourne, one Geelong).
  2. Each district has working interiors, room-based loot, zombie zones and vehicle zones; doors, streets, sidewalks and stairs are usable at gameplay scale.
  3. The player drives the signed Princes Freeway between districts, using a junction, refuelling at a roadhouse and crossing at least one cell seam without stream-in failure.
  4. Uniform-scale and compressed-scale drives are compared (tiles, measured drive time, settlement area) and a scale is chosen from the results.
  5. In-game map covers the pilot area, and save/reload mid-corridor and on a seam resumes the trip.

**Plans**: TBD
**UI hint**: yes

### Phase 3: National Road Network and Regional Production

**Goal**: Players can drive between any two of the twelve mainland destinations on one continuous signed network, with survival stops, in region-by-region increments.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: MAP-01, ROAD-01, ROAD-02, ROAD-03, ROAD-04, SCALE-02, PLAY-01, PLAY-02
**Success Criteria** (what must be TRUE):
  1. Each of the twelve destinations has a documented, recognisable, playable district with spawns, interiors, loot, zombie and vehicle zones.
  2. A player can drive from any destination to any other with no fast travel, following road signs and the in-game map.
  3. Corridors keep pinned junctions, bridges, turnoffs and survival stops, with fuel at intervals that need one refuel per long leg.
  4. Every corridor link driven in both directions passes collision, signage, stream-in and save/reload checks.
  5. Measured drives are about 5 minutes for short links and 20 to 30 minutes for long interstate legs.

**Plans**: TBD
**UI hint**: yes

### Phase 4: Identity and Selective Features

**Goal**: Each destination feels distinct, using only features proven in earlier phases.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: MAP-02, MAP-03, MAP-04, PLAY-03, PLAY-04
**Success Criteria** (what must be TRUE):
  1. Each destination shows a few hand-curated landmarks that identify it (e.g. Sydney harbour, Melbourne grid).
  2. Tropical (Cairns, Darwin) and outback (Coober Pedy, Broome) biomes appear where the tile audit shows they are achievable on vanilla tiles.
  3. Multi-level features (e.g. Coober Pedy dugouts, car parks, overpasses) exist only for proven types, each reachable from its approach road with working entrances, stairs and collision.
  4. Roadside wrecks, roadblocks and a checkpoint appear along corridors, and found in-world maps reveal town outlines.

**Plans**: TBD
**UI hint**: yes

### Phase 5: Release Gate

**Goal**: The full mainland map is verified as one installable, legally clean, reproducible release.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: REL-01, REL-02, REL-03
**Success Criteria** (what must be TRUE):
  1. A full union compile installed on a fresh profile passes the full corridor drive matrix, budget checks and clean-install acceptance.
  2. The licence and attribution audit (OSM/ODbL, Knoxify/KnoxMap, tiles, assets) passes before any distribution.
  3. A repeat export from the same pinned inputs reproduces the validated road layout and preserves manual work.

**Plans**: TBD

### Phase 6: Bass Strait Ferry (Conditional)

**Goal**: Players can cross to Tasmania safely, or the island is left out without affecting the mainland release.
**Mode:** mvp
**Depends on**: Phase 1 (pedestrian proof may start after Phase 2); merge gated after Phase 5
**Requirements**: TAS-01, TAS-02, TAS-03, TAS-04, TAS-05
**Success Criteria** (what must be TRUE):
  1. A pedestrian ferry round trip from a road-accessible terminal keeps inventory and save state intact, including after save/reload.
  2. The terminal states clearly whether vehicles can board, and vehicle, occupant and cargo transfer is tested separately.
  3. If the destination cannot load or has no safe arrival point, the player stays at the departure terminal with a clear message.
  4. Both terminals have usable road approaches and a driveable island road network reaches selected destinations.
  5. Tasmania ships only if the ferry passes; a foot-passenger-only crossing is an acceptable fallback and no mainland requirement depends on it.

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Toolchain Spike and Pipeline Foundations | 8/13 | In Progress | - |
| 2. Melbourne-Geelong Pilot | 0/0 | Not started | - |
| 3. National Road Network and Regional Production | 0/0 | Not started | - |
| 4. Identity and Selective Features | 0/0 | Not started | - |
| 5. Release Gate | 0/0 | Not started | - |
| 6. Bass Strait Ferry (Conditional) | 0/0 | Not started | - |
