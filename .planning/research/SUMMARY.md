# Project Research Summary

**Project:** Project Australia
**Domain:** Real-world-geography Project Zomboid (Build 42) map mod. Multi-city Australia with compressed highway corridors, built from OpenStreetMap data.
**Researched:** 2026-11-09
**Confidence:** MEDIUM

## Executive Summary

Project Australia is a single-player Project Zomboid Build 42 map mod. It covers curated city districts at playable scale, joined by compressed highway corridors (Princes Freeway first), with roadhouses as survival stops and an optional Bass Strait ferry. The closest prior art is Real USA: wide and shallow, auto-generated at 1:40 with about 665 towns, a 9 GB download and a companion jar. Project Australia should take the opposite trade: a small number of hand-curated districts, a compressed and meaningful corridor network, and a vanilla-only install.

Recommended approach: a layered, one-way build. Pinned inputs (dated Geofabrik extract, Build 42.21 Stable, Unjammer PZ Mapping Tools 43.00B261030) feed a small Python generator that owns national geography (route graph, corridor compression, region placement). Generated output lives in a disposable `generated/` tree. Hand work lives in a separate `edits/` overlay tree that is never regenerated over. KnoxMap is a pilot accelerator and reference only, not the production pipeline.

Main risks are technical. (1) Cell format and region merging on one world grid: the research disagrees on 256 vs 300 cells and must be settled in the pilot. (2) Seams: road mismatches at cell boundaries are the top failure mode. (3) Hand-edit loss on regeneration. (4) In-game behaviour community docs cannot confirm: overpass ramps, vehicle ferry transfer, save/reload of edited cells. Treat the pilot as a set of gates, not a milestone.

## Key Findings

### Recommended Stack
- Build 42.21 Stable (pin; recheck 42.22 before final pin)
- PZ Mapping Tools 43.00B261030 (WorldEd, TileZed, BuildingEd); only maintained B42 toolchain; GPL-2.0
- Geofabrik Australia extract, pinned dated `.pbf` with SHA-256; no live fetch in builds
- osmium-tool 1.19.0 + pyosmium 4.3.2
- Python 3.13 with locked venv (shapely, pyproj, numpy, Pillow, networkx)
- Lua (Kahlua) for in-game spawn, sandbox and ferry scripting
- Pin tools zip, SHA-256 and game build together in one `PINS` file. Do not mix tools builds with KnoxMap's patched CLI. Set KnoxMap `auto_update` false if used. No Overpass in production.

### Expected Features
**Table stakes:** multiple curated spawns; clean load and new save; seam-correct roads; loot by building type (RoomDefs); functional interiors on main streets; zombie density zones; vehicle zones; fuel along corridors (one refuel per long leg); readable signage; in-game map coverage with labels; save/reload mid-trip; vanilla-only install with documented steps; OSM attribution.

**Differentiators:** compressed corridors with pinned junctions, bridges and stops (measured against uniform-scale baseline); roadhouses as survival stops (3 to 4 templates); regional biomes (pending feasibility, Real USA needs a companion mod); few high-quality city landmarks; event props (wrecks, roadblocks, Hume military checkpoint); hand-edit-preserving rebuild; optional found-map discovery layer; conditional Tasmania ferry (foot passengers first).

**Defer (v2+):** Z-level features beyond proven types; biomes beyond temperate Victoria until confirmed; random encounters beyond static props; multiplayer and Workshop release; lifts; drivable ship; fast travel; uniform 1:1 scale; filler towns; surveyed interiors.

### Architecture Approach
One-way layered build: `sources -> config -> derived -> composed -> compiled -> installed`. Each stage is a pure function of inputs, config slice and tool version, and skips when the hash matches. A tool writes only to its own output directory. `edits/` is written only by an explicit human `promote` command.

Components: source snapshot (manifest with hash, date, licence); design config (`world.yaml`, `routes.yaml`, `scale.yaml`, `stops.yaml`); geo-processing (sole owner of geography and scale; one continuous road polyline with arc-length compression and pinned anchors; never stitch separate generations); raster and footprint generator (palette-exact BMPs; unknown colour fails); composer (sole merge point, precedence generated < masks < hand TMX < locked); hand-edit overlays with stable anchors; compiler (atomic `releases/<ver>`, `current` repointed only on success); validation gates; separate ferry mod.

One global grid; regions are cell rectangles. Leave gap cells so extensions do not renumber cells. One `.pzw` with per-region compile profiles; full union compile at release.

### Critical Pitfalls
1. Version drift: pin game, tools, tilesheets and generator in `PINS`; disable auto-update on dev machine; fail on unmatched tiles.
2. Generated output as source of truth: separate trees; never save over generated TMX; regen test (regenerate, diff, confirm overlays survive).
3. Seam mismatches: shared connection-point schema; seam validator on every shared edge; drive every seam both ways.
4. Cell count, load and save blowups: measure MB per populated and empty cell, load time and save growth in P0; set budgets; lay out by route order.
5. Compression deleting anchors: piecewise arc-length remap with pinned anchors; one game-km scale for signs.
6. Stream-in and vehicle failures at seams: keep seams straight and simple; test at max speed both ways; save/reload parked on a seam.
7. Ferry stranding or state loss: pedestrian proof first; modData ferry state; safe fallback; foot-passenger-only if vehicles unreliable.

Also: ODbL attribution and derivative obligations (P1 provenance, P5 gate); tile sheet and third-party asset redistribution (asset ledger); Z geometry that vehicles cannot drive (prove each type in P0).

## Implications for Roadmap

### Phase P0: Pilot and Tooling Spike
**Rationale:** Toolchain, cell format and mod layout gate every later decision.
**Delivers:** `PINS` file; one Native256 cell compiled and loaded standalone with no `lots=`; mod folder layout confirmed; MB per populated/empty cell and load time measured; ramp test both ways; ferry-style teleport with save/reload; cell-size decision recorded.
**Avoids:** Pitfalls 1, 4, 10, 16.

### Phase P1: Pipeline, Config and Validation Gates
**Rationale:** Route graph, grid and overlay model are cheap now and expensive to change later.
**Delivers:** `config/` files; design-graph connectivity check (all destinations in one component); `edits/` overlay model with stable anchors, locks and orphan report; provenance, asset ledger and ODbL note; staging build and atomic swap; seam connection-point schema; projection tests against landmarks.
**Avoids:** Pitfalls 2, 3, 6, 7, 8, 12, 13, 14, 15.

### Phase P2: Pilot Vertical Slice (Melbourne, Geelong, Princes Freeway)
**Rationale:** First real test of the whole chain.
**Delivers:** Two districts with interiors, loot, zombie and vehicle zones, two spawns; compressed Princes Freeway corridor with signs, one roadhouse with working fuel, one junction and stop; two-region seam by directory copy; in-game map for pilot area; regen test with a surviving hand edit; uniform baseline; budget table; drive times and fuel test; mid-corridor save/reload.
**Avoids:** Pitfalls 5, 6, 11, 12, 17.

### Phase P3: Validation Hardening and Regional Production
**Rationale:** Scale region by region along a connected chain.
**Delivers:** built-graph connectivity check; seam comparator, palette and budget gates per release; in-game drive harness; regions in route order (for example SA, NSW/ACT, QLD, NT, WA, outliers last); each region ends with a seam test and two-way drive.
**Avoids:** Pitfalls 3, 4, 11, 18, 20.

### Phase P4: Selective Features
**Rationale:** Identity features depend on a stable base and proven tiles.
**Delivers:** corridor biome bands (after tile audit); few city landmarks; Z features only for P0-proven types with entrance and collision tests; event props; optional found-map layer.
**Avoids:** Pitfalls 10, 12.

### Phase P5: Release Gate
**Rationale:** Release is separate from the pilot and needs union compile and full drive matrix.
**Delivers:** full union compile; full corridor drive matrix; budget check against target machine; licence and attribution audit (including Knoxify); clean-install acceptance on fresh profile; re-pin to current Stable; full test suite run.
**Avoids:** Pitfalls 1, 7, 8, 19.

### Phase P6: Bass Strait Ferry (Conditional, Separate Gate)
**Rationale:** Riskiest unknown; must not block mainland.
**Delivers:** separate ferry mod; pedestrian round trip with inventory and save, then vehicle transfer, then failure injection; foot-passenger fallback; Tasmania cell rectangle reserved in P1. Pedestrian proof may start in parallel from P2; merge gated last.
**Avoids:** Pitfalls 9, 10.

### Phase Ordering Rationale
- P0 before P1: cell format and tool pins change the config schema.
- P1 before P2: pilot needs overlay and seam schema.
- P2 before P3: budgets and seam method must be measured before multiplying.
- P4 after base is stable: depends on proven tiles and P0 results.
- P6 parallel to P2 but gated last.

### Research Flags
**Needs research (`/gsd-plan-phase --research-phase`):**
- P0: cell size (256 vs 300), spawnpoints format, mod layout, world-map format, 42.22 status.
- P2: worldmap XML for non-contiguous world; zone and room-def authoring (WorldEd vs Lua); fuel vs sandbox settings.
- P4: biome companion-mod need; foliage tile vocabulary.
- P6: ferry teleport call names (confirm against decompiled Lua); vehicle transfer; save behaviour (LOW confidence).

**Standard patterns (skip research-phase):** P1 (config-as-source, anchored overlays, seam validator, atomic release); P3 (repeat proven loop); P5 (ledger audit, clean-install checklist).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Tool and version facts HIGH; in-game behaviour (ramps, teleport, cell format) MEDIUM or LOW |
| Features | MEDIUM | Real USA facts HIGH (Workshop page); complaints and other specifics LOW-MEDIUM |
| Architecture | MEDIUM | Pipeline shape sound; KnoxMap/Knoxify HIGH (READMEs); B42 compiler and merge unproven |
| Pitfalls | MEDIUM | Ownership, seams, budgets, ODbL grounded; engine claims are training knowledge, prove in P0 |

**Overall confidence:** MEDIUM.

### Gaps to Address
- **Cell size (256 vs 300):** STACK recommends Native256 (game compiles to 256). ARCHITECTURE and parts of PITFALLS assume 300. Resolve in P0 by compiling one cell. Keep cell size a parameter in `world.yaml`.
- **Spawnpoints format:** Native256 `posX/posY/posZ` vs legacy `worldX/worldY`. Check vanilla 42.21 `spawnpoints.lua` in P0.
- **Standalone map without `lots=`:** confirm loads on 42.21 in P0.
- **Multi-region merge:** directory copy with distinct origins. Prove with Melbourne-Geelong seam in P2; multiple map folders is the fallback.
- **Overpass ramps:** community reports of one-sided failure. Test both ways in P0; default to at-grade or visual-only bridges until proven.
- **Ferry teleport and vehicles:** no verified API. Confirm against decompiled Lua; foot-passenger fallback.
- **Worldmap, zones, room defs:** confirm authoring tool and file formats on the pinned build.
- **Biomes:** audit tile vocabulary before promising identity.
- **Knoxify licence:** KnoxMap says none published; GitHub API says MIT. Confirm with author before copying code.
- **KnoxMap licence mix:** patched `worlded/` GPL-2.0-or-later; others MIT. Do not vendor without a licence decision.
- **ODbL posture:** attribution required; publication of derived database depends on posture. Record in P1; legal check before public release (not legal advice).
- **Game point release:** 42.22 is pre-release; recheck Stable before pin.
- **Real USA complaints:** not retrievable; recheck when Steam comments are accessible.

## Sources

### Primary (HIGH confidence)
- PZ Mapping Tools (README, docs, releases, linked world projects): https://github.com/Unjammer/PZ_Mapping_Tools
- KnoxMap (README, packager, placement, LICENSES.md, CHANGELOG): https://github.com/spytheeuclidean-a11y/knoxmap
- Knoxify README: https://github.com/arytek/knoxify
- Geofabrik Australia extract: https://download.geofabrik.de/australia-oceania/
- Real USA Workshop page: https://steamcommunity.com/sharedfiles/filedetails/?id=3829712469
- Release versions via GitHub releases API and endoflife.date

### Secondary (MEDIUM confidence)
- Build 42.21 Stable: https://patchbot.io/games/project-zomboid/articles/1572-build-4221-stable-released
- Build 42.20 stable (search result only): https://projectzomboid.com/blog/news/2026/07/project-zomboid-build-42-20-released/
- PZ Vanilla Map B42 export: https://github.com/Unjammer/PZ_Vanilla_map_b42
- B42 modding structure: https://projectzomboid.wiki/guides/modding-tools/
- OSM copyright and ODbL: https://www.openstreetmap.org/copyright
- B42 maps index (cell size 256, VERIFY): pzfans.com

### Tertiary (LOW confidence)
- 42.22 status: https://patched.gg/games/project-zomboid/42221-pre-release-hotfix-released ; https://supercraft.host/wiki/project-zomboid/build_42_22_pre_release/
- Ferry and vehicle teleport, bridge ramps: Steam Workshop threads only
- Hosting guides (supercraft.host, freakhosting, ggservers)
- Steam discussion: https://steamcommunity.com/app/108600/discussions/1/595153155946204691/
- Engine behaviour: training knowledge, unverified on B42

---
*Research completed: 2026-11-09*
*Ready for roadmap: yes*
