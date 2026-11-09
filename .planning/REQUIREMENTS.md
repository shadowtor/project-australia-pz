# Requirements: Project Australia

**Defined:** 2026-11-09
**Core Value:** Road trips are part of survival: distinct cities and drives between them on physical roads, no mainland fast travel.

## v1 Requirements

### Foundations (BUILD)

- [ ] **BUILD-01**: Game build, mapping tools, generator revision and OSM extract are pinned in one PINS file with checksums, and a build repeats without a live data pull
- [ ] **BUILD-02**: Generated output, scale/route config and hand-authored edits live in separate trees; a regeneration test shows hand edits survive and orphaned edits are reported
- [ ] **BUILD-03**: Design-graph connectivity, seam road comparison, palette/unmatched-tile checks and size/load budgets run as validation gates and report failures by region and cell
- [ ] **BUILD-04**: A failed generation or compile leaves the last playable export installed (atomic release)
- [ ] **BUILD-05**: OSM attribution, extract date/provenance, transformations and a third-party asset/licence ledger are recorded and shown in the mod
- [ ] **BUILD-06**: A clean install can start a new save using documented steps, with no companion mod required

### Pilot (PILOT)

- [ ] **PILOT-01**: One representative Melbourne district and one Geelong district are playable, with interiors, loot, zombie and vehicle zones and two supported spawns
- [ ] **PILOT-02**: A compressed, signed Princes Freeway corridor joins them with a usable junction, a roadhouse with working fuel and at least one map cell seam
- [ ] **PILOT-03**: A uniform-scale baseline and the compressed scale are compared on corridor length in tiles, measured drive time and settlement area represented; the scale is chosen after driving the pilot
- [ ] **PILOT-04**: The pilot area has in-game map coverage, and save/reload mid-corridor and on a seam resumes the trip
- [ ] **PILOT-05**: The pilot records cell format (256 vs 300), cell count, export size, new-save load time and driving performance against agreed budgets on the target machine
- [ ] **PILOT-06**: Ramp/overpass driving, a basement entrance and a ferry-style teleport with save/reload are each proven or ruled out in the pinned build

### Map and scale (MAP, SCALE)

- [ ] **MAP-01**: Melbourne, Geelong, Sydney, Canberra, Gold Coast, Brisbane, Cairns, Darwin, Broome, Perth, Coober Pedy and Adelaide each have a documented, recognisable, playable district
- [ ] **MAP-02**: Each destination has a few hand-curated landmarks that identify it (e.g. Sydney harbour, Melbourne grid)
- [ ] **MAP-03**: Regional biomes (tropical Cairns/Darwin, outback Coober Pedy/Broome) are applied where the tile audit shows they are achievable on vanilla tiles
- [ ] **MAP-04**: Selective multi-level features (e.g. Coober Pedy dugouts, car parks, overpasses) ship only for types proven in the pilot, each connected to its approach road with entrances, stairs and collision tested
- [ ] **SCALE-01**: Streets, lanes, doors, sidewalks and stairs work at gameplay scale; corridors compress length only and blend into city streets at the outskirts
- [ ] **SCALE-02**: Short links take about 5 minutes and long interstate legs about 20 to 30 minutes of driving, measured in-game

### Roads (ROAD)

- [ ] **ROAD-01**: Every mainland destination is reachable by vehicle from every other through one continuous signed highway network with no fast travel
- [ ] **ROAD-02**: Corridors keep pinned junctions, bridges, turnoffs and survival stops (roadhouses, fuel, service towns, rest areas) along real highway alignments
- [ ] **ROAD-03**: Every corridor link is driven in both directions and passes collision, signage, stream-in and save/reload checks
- [ ] **ROAD-04**: Fuel is available at intervals that support one refuel per long leg

### Gameplay (PLAY)

- [ ] **PLAY-01**: Supported spawns, functional interiors, room-based loot, zombie density zones and vehicle zones work on the pinned build
- [ ] **PLAY-02**: Players can navigate by road signs and the in-game map across the whole network
- [ ] **PLAY-03**: Template roadside event props (wrecks, roadblocks, checkpoint) appear along corridors
- [ ] **PLAY-04**: Found in-world maps reveal town outlines (optional discovery layer)

### Release (REL)

- [ ] **REL-01**: A full union compile passes the full corridor drive matrix, budget checks and clean-install acceptance on a fresh profile
- [ ] **REL-02**: A licence and attribution audit (OSM/ODbL, Knoxify/KnoxMap, tiles, assets) passes before any distribution
- [ ] **REL-03**: A repeat export from the same pinned inputs reproduces the validated road layout and preserves manual work

### Tasmania, conditional (TAS)

- [ ] **TAS-01**: A pedestrian ferry round trip from a road-accessible terminal keeps inventory and save state intact, including after save/reload
- [ ] **TAS-02**: Vehicle, occupant and cargo transfer is tested separately; the terminal states clearly whether vehicles can board
- [ ] **TAS-03**: If the destination cannot load or has no safe arrival point, the player stays at the departure terminal with a clear message
- [ ] **TAS-04**: Both terminals have usable road approaches and a driveable island road network reaches selected destinations
- [ ] **TAS-05**: Tasmania ships only if the ferry passes its gate; a foot-passenger-only crossing is an acceptable fallback, and no mainland requirement depends on it

## v2 Requirements

### Release

- **PUB-01**: Steam Workshop publication
- **MP-01**: Multiplayer and dedicated-server support (road traversal, saves, ferry transfer)

### Scope growth

- **MAP-05**: Additional intervening towns and suburbs beyond selective stops
- **MAP-06**: Z-level types beyond those proven in the pilot (e.g. lifts)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full 1:1 or continental Real USA-style scale | Playable scale and compressed corridors are the point |
| Auto-generated filler towns | Dilutes quality; only curated districts and selective stops |
| Mainland fast travel | Roads must be physical |
| Surveyed or fully accurate interiors | Interiors are designed for Zomboid |
| Drivable ship simulation | Ferry is a deliberate two-way transfer |
| Core dependence on a companion jar or mod | Vanilla-only install is a table-stakes goal |
| Period (e.g. 1993) setting | Present-day geography chosen |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (filled by roadmapper) | | Pending |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 0
- Unmapped: 33 ⚠️

---
*Requirements defined: 2026-11-09*
*Last updated: 2026-11-09 after initial definition*
