# Feature Landscape

**Domain:** Large / real-world Project Zomboid (Build 42) map mod, multi-city, road-trip focused
**Researched:** 2026-11-09
**Overall confidence:** MEDIUM (Real USA page fetched directly; Raven Creek / Riverside / Muldraugh-expansion specifics and player complaints rest on thin, mostly secondary sources and modding knowledge. Real USA's 497 Workshop comments were not readable.)

## Reference: how Real USA handles scale (HIGH, from Workshop page)

- Lower 48 as one B42 world at **1:40**; 1 tile = 40 m; 120,832 x 77,824 tiles (472 x 304 cells). Roughly 665 towns at real locations; only the largest get street grids and landmarks.
- **19 curated start locations** (desert rest stop to small towns), not a city-wide spawn free-for-all.
- Interstates, major rivers, bridges, gas stations, rest stops, wrecks, police stops, military checkpoints. Wilderness follows real land cover (desert, plateau, Rockies, plains, eastern woods), which **requires a companion mod (ZombieBuddy)** plus an approved .jar.
- Set-piece content: 12 military bases, 13 hospitals, airfields (optional Cessna mod), closed border with customs stations, end-game site (Area 51).
- **In-world town maps** found in gas stations, shops, offices, homes and glove boxes reveal a town's outline. This is its navigation/discovery mechanic.
- Cost: **9.1 GB download**, first world load takes minutes, 16 GB RAM recommended, -Xmx6g to -Xmx8g advised. Most of the map runs like vanilla; the biggest cities stutter and load slowly.
- Author-stated weaknesses: early beta, auto-generated from real data, odd roads and broken buildings, not widely played.

Takeaway for Project Australia: Real USA is wide and shallow (auto-generated, mostly thin towns). Australia's differentiator is the opposite trade: 12 hand-curated districts plus a compressed, meaningful corridor network. Do not chase its town count.

## Table Stakes

Missing = players uninstall or the map is unplayable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multiple curated spawn points (per city + a few roadside/outback starts) | Every map mod ships spawn regions; players pick a start in the character-creation list. Spawn regions only affect new characters. | Low | One spawn-regions Lua entry per start. Needs safe, indoor-reachable tiles. Verify the exact file/API against the official wiki for the pinned build; hosting guides conflict on filenames (MEDIUM). |
| Map loads and a new save starts cleanly with the mod enabled | Basic. Large maps notoriously fail here (load stalls, "interior map hasn't loaded"). | High | Gate on measured load time and RAM on target machine. See Pitfalls. |
| Continuous collision-correct roads with no dead ends at cell seams | Core promise of the project. Seam breaks are the top failure mode of stitched maps. | High | Validate both sides of every seam; script a road-connectivity check. |
| Loot distribution that matches building type | Players loot by building category (fast food, hardware, pharmacy, servo, police). Without room-def/zone tagging, buildings are empty or generic. | Med | Room names (RoomDefs) drive vanilla loot. Do it per interior; reuse vanilla room names. |
| Functional building interiors (doors, windows, stairs, lights, containers) on at least the main streets | "Loot a neighbourhood" is the first-minute experience. Empty shells = broken. | High | Biggest labour sink. Mix of imported footprints plus template interiors; hand-fix landmarks. |
| Zombie population zones / density tuning | Vanilla zombie spawn is map-zone-based; without it large rural areas are empty or cities overwhelm the engine. | Med | Map-level zone definitions (urban dense, town medium, highway sparse, outback near-empty). Tie to sandbox defaults. |
| Vehicle spawn zones (cars on roads, car parks, driveways, servos) | A road-trip map with no cars is a walking sim. | Med | Vehicle zones + type mix (regional: utes/4WD, road trains optional). Needs a vehicle-supply-per-city check. |
| Fuel stations with working pumps and enough fuel availability along corridors | Driving long legs requires refuel. Players complain loudly when fuel is absent or gas stations are fake. | Med | Place servos/roadhouses at fuel-range intervals; the compressed corridor must still demand one refuel on long legs. Check pump behaviour against the sandbox "fuel/utilities" shutoff settings. |
| Readable road signage (route numbers, destinations, distances, junction signs) | "Navigate by signs" is an explicit acceptance criterion. Real USA relies on interstates plus maps. | Med | Needs custom signage tiles/sprites (check licences); consistent style; destination signs before every junction. |
| In-game world map coverage (map reveal / annotations) | B42 world map is a core player tool. Players expect roads, towns, labels on it; mods that omit it feel blind. | Med-High | Needs map image/data for the custom world and named places. Real USA also hides town outlines behind found maps. Decide reveal model early (see Differentiators). Mapping API details are a gap (see below). |
| Save/reload resumes mid-trip safely | Stated acceptance criterion. Streaming unloaded far cells breaks vehicles and saves when mods mis-handle them. | Med | Test parked-vehicle persistence across seams. |
| Mod installs from a clear folder/Workshop layout with documented dependencies | Real USA needs a companion jar and a 9 GB download, and it shows in complaints. Clarity is expected. | Low | Local install first; documented steps in README. |
| Credits and OSM attribution | Legal baseline. | Low | In-mod credits file plus README. |

## Differentiators

Not expected, but they are why someone picks this map over Real USA.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Compressed highway corridors (selective scale, blended at outskirts) | The project's core: drives are worth taking (5 min short / 20-30 min long) instead of Real USA's 1:40 empty distance or uniform scale that wastes time. | High | Pilot must compare against a uniform baseline. Keep real junction order, bridges and turnoffs. |
| Roadhouses and service towns as survival stops (fuel, food, bed, loot, set-piece danger) | Turns corridor into gameplay beats; unique Australian outback texture (Nullarbor, Stuart Hwy). Uncommon in other PZ maps. | Med | Reusable roadhouse template with 3-4 variants; place at fuel-range intervals. |
| Regional biomes and vegetation (tropical Cairns/Darwin, red-earth outback, temperate Vic, bush NSW, arid WA) | "Landscape changing" is the stated Core Value. Real USA does this with a companion mod (ZombieBuddy). | High | Tile/vegetation set per region; weather/temperature variants only if the build exposes them. Needs a Pilot-phase feasibility check on whether it needs a companion mod. |
| Recognisable landmarks per city (harbour/Opera House area, MCG/Flinders, Parliament House, Big Pineapple-style roadside icons, Coober Pedy dugouts) | Gives each city a hook; makes screenshots shareable. | Med-High | Few, high quality; do not spread thin. Landmark list is an open question in PROJECT.md. |
| Selective multi-level features (car parks, overpasses, Coober Pedy dugouts, basements) | Rare in map mods; gives Coober Pedy identity. | High | Depends on B42 Z-level support in tooling. Each must connect to its approach road and be tested. |
| Ferry crossing to Tasmania (Spirit of Tasmania-inspired) | Memorable set piece; sells the whole idea. | Very High | Conditional (TAS-01). Pedestrian round trip first; vehicles separate. Needs scripted teleport plus a safe-arrival fallback. |
| Discovery-based map reveal (found road atlases / servo maps) as in Real USA | Lets players earn knowledge; reinforces road-trip feel. | Med | Optional layer on top of base in-game map. Do not make it mandatory for route finding when signs exist. |
| Region-specific encounters (outback breakdown, roadkill/quarantine road-block, military checkpoint on Hume, quarantine fence at borders) | Fills long legs with beats. Real USA does police stops, military checkpoints and wrecks. | Med | Template-based event props (wrecks, barricades); no scripted AI. |
| Hand-edit-preserving rebuild pipeline | Lets the map evolve without throwing away work; rare in generated maps. | High | Listed under BUILD-01. Infrastructure, not player-visible, but it is why quality can compound. |

## Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| 1:1 or Real USA-style continental 1:40 scale | Explicit non-goal. Huge cell counts, minutes-long loads, 9 GB downloads, mostly empty land. | Compressed corridors plus playable-scale cities. |
| Auto-generated filler towns across the whole route | Real USA admits odd roads and broken buildings from generation; dilutes quality and file size. | A small set of curated roadhouses/service towns only. |
| Fast travel (teleport) on the mainland | Violates Core Value. | Physical roads only; scripted travel only for the Bass Strait ferry. |
| Dependence on a companion script/jar mod for core function | Real USA needs ZombieBuddy plus a jar approval; raises install friction and breakage on updates. | Stay in vanilla map modding; only add a dependency if a feature is impossible otherwise and record it in the pilot. |
| Surveyed-accurate interiors | Non-goal; huge labour for no gameplay value. | Designed-for-Zomboid templates. |
| Drivable ship simulation | Non-goal. | Static ship area with a deliberate transfer. |
| Multiplayer and Workshop release at the start | Out of scope; multiplies testing (server, desync, seams). | Single-player local first. |
| Every suburb and intervening town | Non-goal; wastes cell budget. | Representative districts plus selective stops. |
| Hardcoded absolute loot/zone tuning per tile | Unmaintainable at scale. | Zone- and room-type based rules. |
| Unlimited vehicle/zombie density in cities | Largest Real USA cities stutter. | Per-city budgets and measured density caps. |

## Common Complaints in Large Maps (and what to design against)

Confidence MEDIUM-LOW: grounded in Real USA's own known-issues text, forum search snippets and general PZ community knowledge; no deep review of the 497 Real USA comments was possible.

| Complaint | Design response |
|-----------|-----------------|
| Very long first load, big RAM needs, stutter in large cities (Real USA's NYC/Chicago/Las Vegas) | Set budgets in the pilot; cap city size; document -Xmx settings. |
| Huge download (9 GB) | Budget disk footprint; compress terrain and reuse tiles. |
| Broken roads, odd building geometry, missing interiors from generated content | Hand-validate all drive routes; automated connectivity check; don't ship unreviewed generated areas. |
| Required companion mods, jar approvals, version breakage after game updates | Pin build; minimise dependencies; document. |
| Empty land / boring long drives | Corridor compression plus roadhouses/events. |
| Each location as a separate mod, load-order conflicts (Raven Creek-style overhauls adding memory pressure) | Single package, documented load order, bounded footprint. |
| Spawn locations unsafe or inside walls; spawn regions missing for new maps | Test every spawn on a clean save. |
| Vehicles or players lost at cell boundaries | Seam tests both directions; save/reload at seam. |

## Feature Dependencies

```
Pinned build + tools + coordinate/cell grid
  -> Terrain & road network (with seams)
       -> Signage            (needs route graph)
       -> Fuel / roadhouses  (needs road network + corridor lengths)
       -> Vehicle zones      (needs roads + parking/driveway tiles)
       -> In-game world map  (needs final geometry + place names)
  -> Building footprints
       -> Interiors -> Room defs -> Loot tables
       -> Zombie zones (needs zone layer + cell layout)
  -> Spawn points (needs safe interiors + loot + zombie zones in place)
Multi-level features -> build Z-level support + approach roads
Regional biomes -> tile/vegetation set (may need a companion mod: pilot check)
Ferry -> terminals on both sides + Tasmanian road network + scripted transfer + save-state proof
Hand-edit-preserving rebuild -> layered editable sources (before large-scale content)
```

## MVP Recommendation

Prioritise (matches PILOT-01):
1. Road continuity + seam-safe Princes Freeway corridor with signs and one roadhouse/servo with working fuel.
2. Two curated districts (Melbourne, Geelong) with functional interiors, loot, zombie zones, vehicle zones and 2 spawn points.
3. In-game map covering the pilot area, plus save/reload of a mid-corridor trip.
4. One differentiator: compressed corridor (measured vs uniform baseline).

Defer: ferry/Tasmania (conditional, late gate); biomes beyond temperate Victoria until pilot confirms tile/companion-mod feasibility; multi-level features (do Coober Pedy dugouts and car parks only after build Z-level support is proven); Real USA-style found-map discovery layer; random encounters beyond static wrecks and roadblocks.

## Gaps (need phase-specific research)

- How B42 world map data and annotations are authored for custom maps (API/file names unverified; sources gave nothing on this).
- Whether zombie zone, vehicle zone and room-def authoring is done in TileZed/WorldEd or via Lua for the pinned build, and B42 changes to them.
- Whether regional biomes/vegetation need a companion mod (Real USA uses one).
- Real player complaints in Real USA's comments, Raven Creek and Riverside threads (not retrievable here); re-check once access to Steam comments is available.

## Sources

- Real USA Workshop page (fetched directly): https://steamcommunity.com/sharedfiles/filedetails/?id=3829712469 (HIGH for stated facts)
- PZ Steam discussions on B42 performance and map loading: https://steamcommunity.com/app/108600/discussions/1/595153155946204691/ (LOW-MEDIUM)
- Hosting guides on B42 tuning and spawn regions (supercraft.host wiki, freakhosting, ggservers): MEDIUM-LOW, commercial secondary sources
- Project docs: .planning/PROJECT.md, PROJECT-AUSTRALIA-GSD-BRIEF.md
