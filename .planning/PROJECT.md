# Project Australia

## What This Is

A standalone Project Zomboid (Build 42) map mod that recreates twelve mainland Australian cities and towns as playable survival districts, joined by one continuous, driveable highway network. Players loot a neighbourhood, find a vehicle, follow a recognisable highway to another city and carry on in the same save. Tasmania, reached by a Spirit of Tasmania-inspired ferry from Devonport/Geelong, is a separate late feasibility decision. Single-player, locally installable first.

## Core Value

Road trips are part of survival: distinct cities, and drives between them that show the landscape changing, all on physical roads with no fast travel on the mainland.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **MAP-01**: All twelve mainland destinations (Melbourne, Geelong, Sydney, Canberra, Gold Coast, Brisbane, Cairns, Darwin, Broome, Perth, Coober Pedy, Adelaide) have recognisable, playable districts
- [ ] **ROAD-01**: Every mainland destination is reachable by vehicle from every other through the highway network, with signed highways and useful stops (roadhouses, fuel, service towns, rest areas)
- [ ] **SCALE-01**: Streets and buildings work at gameplay scale; cities and corridors scaled separately; drive times and map budgets measured against agreed targets
- [ ] **PLAY-01**: Supported spawns, interiors, loot, zombie populations, vehicles and in-game navigation (signs, in-game map) work on the pinned build; save/reload resumes the trip
- [ ] **BUILD-01**: Map can be rebuilt and exported with hand edits intact, documented dependencies and source credits (OSM attribution, third-party code/tiles tracked)
- [ ] **PILOT-01**: First playable slice: one representative district each in Melbourne and Geelong joined by a compressed Princes Freeway corridor (usable junction, roadside stop, at least one cell seam), used to choose build, tools, scale and quality bar
- [ ] **TAS-01** (conditional): If included, Tasmania has a safe two-way ferry connection from a road-accessible terminal and a driveable island road network to selected destinations; clear message and safe fallback if arrival fails

### Out of Scope

- Full 1:1 Australia — playable scale and compressed corridors are the point
- Every suburb or intervening town — only selective stops that serve navigation and survival
- Fully accurate interiors — interiors are designed for Zomboid, not surveyed
- Drivable ship simulation — ferry is a deliberate two-way transfer
- Multiplayer and Workshop publication — separate release decisions; start with local single-player pilot
- Period (e.g. 1993) setting — present-day geography chosen

## Context

- Inspired by **Real USA** (1:40 Build 42 map, early beta) as a large-world scope/scale reference.
- Prior art/tools to evaluate: **Knoxify** (rasterises real geography to WorldEd BMPs), **KnoxMap** (Build 42 workflow from terrain through buildings, compile, install), **TileZed/WorldEd** (hand editing, inspection, export).
- OpenStreetMap is optional source geography for street patterns, coastlines, waterways, footprints and major routes; ODbL obligations must be verified for the distributed map and any derived database.
- Highway alignments to use as references (e.g. Princes Freeway Melbourne–Geelong); route graph agreed during discovery. Preserve local identity: Melbourne's grid, Sydney's harbour, Cairns' tropical vegetation, Coober Pedy's outback and dugouts.
- Selective Z-levels (car parks, overpasses, basements, Coober Pedy dugouts) only where the build supports them; each connected to its approach road and tested.
- Ferry: road-accessible terminal and static ship/boarding area; Geelong–Devonport proposed. Prove pedestrian round trip (inventory + save intact) first, then vehicles/occupants/cargo separately. Foot-passenger crossing acceptable fallback; defer if passengers can get stranded.
- Reference: [Spirit of Tasmania terminal information](https://www.spiritoftasmania.com.au/sailing-information/terminal-information/).
- Unresolved for phase discussion: which neighbourhoods and landmarks define each destination; which optional layers are worth making playable; Tasmanian destinations beyond Devonport.

## Constraints

- **Game build**: Latest Build 42 stable, exact release pinned during pilot — reference maps target B42
- **Tooling**: Game, mapping tools, generator revision and OSM source snapshot all pinned; same world grid across exported regions; coordinate system, transforms, cell layout and road connection points recorded
- **Reproducibility**: Pinned local source snapshot so builds repeat without a live data pull; last playable export preserved if generation or compilation fails
- **Editability**: Source snapshot, scale/route config and hand-authored edits kept separate so regeneration preserves curated roads, buildings, landmarks; editable layers for terrain, roads, vegetation, buildings, gameplay zones
- **Performance budgets**: Compiled cells, disk footprint, new-save load time and driving performance set on the target machine and measured, not assumed
- **Drive-time targets**: ~5 min for a short link (Melbourne–Geelong), ~20–30 min for a long interstate leg; final scale chosen after driving the pilot and comparing with a uniform-scale baseline
- **Setting**: Present-day Australia (modern roads, footprints, landmarks)
- **Licensing**: OSM attribution included; redistribution rights for third-party code, tiles and assets verified before bundling
- **Routes**: Mainland is one connected world of physical roads; scripted travel reserved for the Bass Strait crossing only
- **Delivery**: Operational completion — a playable export installed and tested in the target build; images, editor previews and compiles are only intermediate evidence

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Scale cities and corridors separately (compressed highways, playable-scale neighbourhoods, blended at outskirts) | Keeps lanes, doors, stairs usable and cities recognisable while making drives worth taking | — Pending (decide after pilot drive vs uniform baseline) |
| Mainland routes remain physical; export and test by region, validating both sides of every seam | No fast travel; seams are a known failure point | — Pending |
| Keep generated geography editable and separate from hand edits | Regeneration must not destroy curated work | — Pending |
| Prototype Bass Strait crossing separately as a late feasibility gate | Ferry scripting, vehicle transfer and save behaviour need their own in-game proof | — Pending |
| Present-day setting | Modern OSM data usable as-is; Geelong–Devonport reference valid | — Pending |
| Build 42 latest stable, standalone single-player start | Matches reference maps; smallest scope for pilot | — Pending |
| Drive-time targets ~5 min short / ~20–30 min long | Road trip must feel like survival, not a chore | — Pending (validate in pilot) |
| Tasmania: include only if ferry round trip proven safe; foot-passenger fallback acceptable | Avoid stranding players | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-09 after initialization*
