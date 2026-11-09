# Technology Stack

**Project:** Project Australia (Project Zomboid Build 42 real-world Australia map mod)
**Researched:** 2026-11-09
**Overall confidence:** MEDIUM. Tool and version facts are HIGH (read from the repos and release feeds today). In-game behaviour (vehicle ramps, ferry teleport, 256 vs 300 cells) is MEDIUM or LOW because the official Build 42 modding docs are thin and the Indie Stone sites blocked automated fetching.

## Headline Recommendation

Do not adopt KnoxMap as the production pipeline. Use it as the pilot accelerator and the working reference for "OSM to compiled B42 map mod". Own the national layout (route graph, corridor compression, region placement) in a small pinned Python generator, and use the Unjammer PZ Mapping Tools (WorldEd/TileZed/BuildingEd) for hand edits and Generate Lots.

Why: KnoxMap is built for "one real place, a few km², uniform 1:1 scale". It has no concept of compressed corridors, a national route graph, or multi-region seams, and it releases almost daily (1.8.5.3 to 1.8.5.5 in 48 hours) with auto-update on by default. That is hostile to the "pinned, reproducible" constraint. It is still the best working example of every step (OSM to BMP to buildings to compile to mod folder), so reuse its ideas and, where licences allow, its tools.

## Recommended Stack

### Game and mapping tools (all pinned)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Project Zomboid (Steam) | **Build 42.21 Stable** (released 2026-09-28) | Target runtime | Build 42 went Stable with 42.20 on 2026-07-29; 42.21 is the latest Stable. 42.22 is on the Pre-Release branch (42.22.1 hotfix 2026-11-04), not Stable. Pin 42.21.x for the pilot; re-test when 42.22 reaches Stable. | HIGH (42.21), MEDIUM (42.22 status) |
| PZ Mapping Tools ("PZTools Unofficial": PZWorldEd, TileZed, BuildingEd) by Unjammer/Alree | **43.00B261030** (2026-11-02); KnoxMap pins **43.00B260909** | Hand editing, BMP-to-TMX, Generate Lots, linked projects, spawnpoints, in-game map | Only maintained toolchain with Build 42 support: basements/negative levels, native 256-cell projects, B42.20 biome map, WorldGen editor, 42.22 tile definitions. GPL-2.0, Windows x64, bundles Qt and VC runtime (no redistributable install needed). The "43.00" is the tools' own label, not a game version. | HIGH |
| Official Indie Stone TileZed/WorldZed | Not pinned | Fallback only | The Indie Stone said it is updating the tools for the 42.20 tile library, but no stable direct download or version was verifiable. The old Unjammer/TileZed B42 fork is archived (read-only). | LOW |
| Extracted tile sheets | From your own install | Tools need PNG tile sheets | Never redistribute (The Indie Stone copyright). The tools' Initial Setup points at the extracted Tiles directory. | HIGH |

Pin rule: store the tools zip, its SHA-256 and the game build number in the repo. Do not mix a newer tools build with KnoxMap's patched `PZWorldEd_cli.exe`, which links against the 260909 release's Qt libraries.

### OSM source and extraction

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Geofabrik Australia extract | `australia-oceania/australia-latest` (currently `australia-261108.osm.pbf`) | Single pinned OSM snapshot | One national file means one provenance record, one date, one ODbL attribution. Save the dated file (the `-latest` URL redirects to a dated name) and its SHA-256, and never fetch live during a build. | HIGH |
| osmium-tool | **1.19.0** (2026-01-18) | Clip per-region and per-corridor extracts, filter tags (`extract -b/-p`, `tags-filter`) | Standard, fast, scriptable CLI. | HIGH |
| pyosmium | **4.3.2** (2026-10-18) | Read PBF directly from the generator | Same library KnoxMap uses for Geofabrik reads. | HIGH |
| GDAL/OGR | **3.13.3** (2026-08-18) | Raster/vector transforms, reprojection, optional DEM or land cover | Only needed if you add elevation or land cover. PZ has no terrain height, so this is optional. | MEDIUM |
| QGIS | 3.44.x (latest tag `final-3_44_15`, 2026-09-25) | Visual QA of the route graph, regions, seams | Inspection only. Do not make it part of the build. | MEDIUM |
| Overpass API | n/a | Do not use for production | Rate limits and cooldowns, and live data breaks reproducibility. Acceptable only for quick throwaway pilot probes. | HIGH |

### Generator scripting

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | **3.13.x** (3.14.10 is current, 3.12+ is the floor KnoxMap needs) | All generators (route graph, corridor compression, raster, config) | Same language as Knoxify/KnoxMap, so their code is directly readable and reusable. Pin a venv with `requirements.lock`. | HIGH |
| shapely, pyproj, numpy, Pillow, networkx | Pin at install | Geometry, CRS transforms, BMP/PNG raster output, national route graph and connectivity checks | Standard geospatial Python. `networkx` gives the "every destination reaches every other" check ROAD-01 needs. Versions were not verified today; lock them at install. | MEDIUM |
| Lua (in-game) | Game's embedded Kahlua | Spawn, sandbox, ferry scripting | Only option inside PZ. | HIGH |

Skip: Blender (not needed), any Node toolchain for generators, a database (osm2pgsql 2.3.1 / PostGIS) unless corridor queries outgrow pyosmium. YAGNI for the pilot.

### Prior-art tools

| Tool | Version | Role | Verdict | Confidence |
|------|---------|------|---------|------------|
| KnoxMap (spytheeuclidean-a11y) | **1.8.5.5** (2026-11-08); 344 stars | Full OSM to B42 mod: terrain, furnished buildings with real heights up to 31 storeys, cars, petrol stations, bridges and overpasses, in-game map, spawn pyramid, Rust compiler option, patched headless WorldEd | **Use for the Melbourne and Geelong pilot districts and as a reference.** Turn `auto_update` off in `knoxmap_config.json`. Project Zomboid B42 only, Windows/Linux/macOS. Multiplayer untested. Its own README says most output is "checked by tools rather than by playing" (kerb orientation, lifts, overpass driving unconfirmed in-game). | HIGH (facts), MEDIUM (quality) |
| Knoxify (arytek) | MIT per GitHub API, pushed 2026-09-27 | OSM to three BMPs (`<map>.bmp`, `_veg.bmp`, `_ZombieSpawnMap.bmp`), exact PZ palette | **Reference for the palette and BMP-to-TMX flow only.** It does not make buildings. Licence conflict: KnoxMap's LICENSES.md says Knoxify "has not published a licence" while the GitHub API reports MIT. Resolve before reusing code. | MEDIUM |
| PZ Vanilla Map B42 (Unjammer) | B4220.3 (2026-08-19) | Vanilla map as an editable WorldEd project | **Study how vanilla builds roads, junctions and cell seams.** Copyright is The Indie Stone's; do not ship. | HIGH |
| PZ Reverse Mapper | n/a | Compiled map back to TMX | Debugging tool for inspecting compiled output. | MEDIUM |

KnoxMap licence picture (matters for BUILD-01): its own additions are MIT, the `worlded/` compiler patch is GPL-2.0-or-later, and the Knoxify-derived files are unlicensed or MIT depending on the reading. Generated maps carry OSM data, so ODbL attribution applies. KnoxMap writes an `ATTRIBUTION.txt` and credits in `map.info`.

## Cell grid: the decision that must be made in the pilot

- Vanilla Build 42 compiles to **256-tile cells** (78 x 63 compiled cells for Knox County). Mapping tools now have a **Native256** project mode, with one source cell mapped to one output cell and `spawnpoints.lua` written with absolute `posX/posY/posZ`.
- KnoxMap authors in **300-tile cells** (legacy) and its compiler resamples them into 256-tile game cells; it notes "300 does not divide into 256", so moving a built map means recompiling.
- TMX maps are capped at 300 x 300 tiles even in Native256 workflows.
- **Recommendation:** make Native256 the project format for the national map, because it is what the game compiles to and removes a resampling step at every seam. Use KnoxMap only for pilot districts and then re-author or convert them. Confidence: MEDIUM. Official Build 42 docs on the cell format were not reachable, so confirm in the pilot by compiling one 256 cell and loading it.
- Seams to test: `chunkdata_*.bin` and 8x8-tile chunk alignment. Both Knoxify and the tools document this; the tools' "Partial Chunks" mode exists for it.

## Combining regions on one world grid

- The game has **one world grid shared by every installed map**; each project declares a **World origin** (in cells) in its Generate Lots settings (`<worldOrigin origin="x,y"/>` in the `.pzw`). Region origin plus per-region local coordinates gives the single national coordinate system. Record these in a committed `world-grid.json`.
- WorldEd **Linked World Projects** (World menu) shows other PZW projects as read-only references, placed by origin difference. It forbids mixing Native256 and Legacy300. Linked cells are not exported. Use it for seam alignment checks only.
- **Production layout:** one mod, one map folder, one `.pzw` per region exported with distinct, non-overlapping origins into the same lots output directory. Lot files are named by absolute cell (`world_x_y.lotheader/.lotpack`), so regions merge by directory copy. Confidence MEDIUM. This is inferred from the file naming and KnoxMap's multi-map placement code, not from an official doc. Prove it with the Melbourne + Geelong seam.
- **Do not place Australia at real relative distances.** KnoxMap caps map origins at cell 400 because the game holds a grid covering every cell any map uses. A map far out makes a world "almost entirely of nothing". Use a schematic national layout (compressed corridors, preserved bearings and route order) that fits a bounded grid. Vanilla Knox County is about 20,000 x 16,000 tiles; budget the national bounding box against that and measure load time.
- Hand edits stay safe by keeping three separate trees: `source/` (OSM snapshot plus config), `generated/` (disposable regenerated BMP/TMX), `curated/` (hand-edited TMX/TBX/Lua). The generator writes only to `generated/` and the build overlays `curated/`. WorldEd Cell Move/Copy/Paste preserves the full cell payload; the Project Doctor and `.pztools-backups` snapshots help. The tools also offer **Generate Lots `.source` text export/import** (`--export-lot-sources`), which makes compiled output diffable and is a good cheap regression check.

## Mod structure for Build 42 (verified against KnoxMap's packager)

```
<modid>/
  mod.info                      # copy in root, common/ and 42/ (a root-only mod.info left KnoxMap mods invisible)
  common/mod.info
  common/media/maps/<Map Name>/
     map.info                   # title=, lots=Muldraugh, KY (omit if standalone), fixed2x=true, description=
     *.lotheader  *.lotpack  chunkdata_*.bin
     spawnpoints.lua            # no spawnpoints = map not offered on the new-game screen
     objects.lua  worldmap.xml  streets.xml  worldmap-annotations.lua  roomtones.lua
     spawnSelectImagePyramid.zip   # optional picture for the spawn picker
  42/mod.info
  42/poster.png
  42/media/lua/{client,server,shared}/   # ferry, sandbox hooks
```

- The `42/` version folder is mandatory for Build 42; `common/` holds shared content. Confidence: HIGH (multiple sources agree; KnoxMap observed the invisible-mod failure).
- `lots=` inherits room and tile definitions from vanilla. A standalone map that leaves `lots=` out inherits nothing from Knox County, which suits this project; confirm it still loads under the 42.21 vanilla, as KnoxMap supports a "standalone" flag but the README does not state the exact guarantee. MEDIUM.
- `spawnpoints.lua` in Build 42 uses **absolute world tile coordinates**. Native256 output uses `posX/posY/posZ`; legacy output used `worldX/worldY` in 300-tile cells. LOW-MEDIUM: verify against the 42.21 vanilla `spawnpoints.lua`.
- Save worlds are written cell by cell as the player walks. **A map changed after a save was made leaves old cells beside new ones with no repair**, so every map rebuild requires a new save. Bake this into the test protocol.
- Sandbox and multiplayer: single-player first. The server-side `Map=` and `_spawnregions.lua` wiring (map folder ahead of `Muldraugh, KY`) is documented in KnoxMap's packager but out of scope here.
- Users launch with a custom `-cachedir` only if the mod is installed outside `%USERPROFILE%\Zomboid\mods`. For local testing, install into `Zomboid/mods`. Build 42 reads the mods folder only at startup.

## Z-levels, vehicles and the ferry

| Topic | Recommendation | Confidence |
|-------|----------------|------------|
| Basements and negative levels | Supported by Build 42 and the tools (RoomDefs on all levels, basement export in BuildingEd, `Basement` zone). Use for Coober Pedy dugouts and car parks. | HIGH (tooling), MEDIUM (in game) |
| Overpasses, ramps | KnoxMap lifts overpasses one or two storeys on **Build 42 ramp tiles**, which it says carry players and cars, but states it has **not driven them in game**. A community B42 map reports bridge ramps failing on one side. Treat every ramp as unproven. Build one test overpass in the pilot and drive it both ways at speed before committing to a design. | LOW |
| Building heights, lifts | KnoxMap supports up to 31 storeys. Lifts need the third-party Elevators mod. Skip lifts. | MEDIUM |
| Vehicle spawns | Use WorldEd zones: `ParkingStall`, `TrafficJam`, `Vehicle`. The tools preview them with the game's vehicle scripts. "No vehicles spawning in B42" is a known failure; verify `VehicleZoneDefinition` zone names. | MEDIUM |
| Ferry, pedestrian | Lua in `42/media/lua/client`: fade screen, request target chunk load, wait until `getCell():getGridSquare(x,y,z)` is non-nil, then set `setX/setY/setZ` plus `setLx/setLy/setLz` on the player. Community reports show interior-teleport mods break on off-by-offset placement and on vehicle exit timing. Confirm the call names against decompiled game Lua; the Javadocs were blocked. | LOW-MEDIUM |
| Ferry, vehicle | Separate prototype. Treat vehicle teleport as likely unreliable (occupants, trailers, chunk load, save/reload). Foot-passenger fallback is the plan. `loadstring/loadstream` were disabled in 42.20.4 and re-enabled in 42.21, so never depend on them. | LOW |
| Ferry placement trick | Put the Tasmania terminal cells physically close to the Victorian coast on the world grid, so the "teleport" is short and both ends stay in or near streaming range. This removes most of the long-distance chunk loading risk. Needs an in-game proof. | MEDIUM (design inference) |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Map pipeline | Own Python generator + PZ Mapping Tools, KnoxMap for pilot districts | KnoxMap as the whole pipeline | No corridor compression or national graph; daily release churn; mixed licences; multiplayer and in-game fidelity unproven |
| Map pipeline | same | Knoxify BMPs only | No buildings, no road semantics beyond colours, Flask UI we do not need |
| Mapping tools | Unjammer PZ Mapping Tools 43.00B261030 | Official TileZed/WorldEd | No verifiable current download or version for B42 |
| Mapping tools | same | Old Unjammer/TileZed B42 fork | Archived 2025/2026, superseded |
| OSM source | Pinned Geofabrik PBF | Overpass live | Rate limits, not reproducible |
| OSM tooling | osmium-tool + pyosmium | osm2pgsql + PostGIS | Heavy for a pilot; add only when queries need it |
| Cell format | Native256 | Legacy300 (KnoxMap default) | Resampling at every seam, 300-vs-256 misalignment |
| Compiler | WorldEd Generate Lots (and KnoxMap's patched CLI for headless) | KnoxMap Rust compiler | Faster, but a single-maintainer tool with mixed licence; adopt only if WorldEd compile time blocks iteration |

## Installation

```bash
# Generator environment (Windows, Python 3.13)
python -m venv .venv
.venv\Scripts\activate
python -m pip install osmium shapely pyproj numpy pillow networkx
python -m pip freeze > requirements.lock

# OSM tooling (osmium-tool 1.19.0 via your package manager or conda-forge)
# Snapshot
curl -L -o data/australia-261108.osm.pbf https://download.geofabrik.de/australia-oceania/australia-261108.osm.pbf

# Mapping tools: download PZ_Mapping_Tools_build20261030.zip (or 260909 if using KnoxMap's patched CLI)
# from https://github.com/Unjammer/PZ_Mapping_Tools/releases and record its SHA-256.
```

## What NOT to Use

- Build 41 mapping tools or Build 41 mod layouts (no `42/`, no basements, 300 only).
- KnoxMap auto-update in the production build (set `"auto_update": false`).
- Live Overpass or "latest" Geofabrik URLs inside a build script.
- Any redistribution of tile sheets, vanilla map exports or KnoxMap's bundled third-party tiles.
- Uniform 1:1 Australia: bounding box and load time make it infeasible, per the brief.

## Open Items for the Pilot

1. Compile one Native256 cell and confirm it loads on 42.21 stable, standalone with no `lots=`.
2. Confirm a two-region seam (Melbourne to Geelong) merges by directory copy with distinct origins.
3. Drive one KnoxMap-style overpass ramp both ways.
4. Pedestrian ferry teleport round trip with a save/reload.
5. Measure compile time, disk size and new-save load time for the pilot, then extrapolate to the bounded national grid.
6. Verify Knoxify's licence with the author before copying code.
7. Re-check 42.22 Stable status before pinning the final release build.

## Sources

- Build 42.21 Stable (28 Sep 2026): https://patchbot.io/games/project-zomboid/articles/1572-build-4221-stable-released (MEDIUM)
- Build 42.20 stable (29 Jul 2026): https://projectzomboid.com/blog/news/2026/07/project-zomboid-build-42-20-released/ (search result only, MEDIUM)
- 42.22 pre-release and 42.22.1 hotfix (4 Nov 2026): https://patched.gg/games/project-zomboid/42221-pre-release-hotfix-released , https://supercraft.host/wiki/project-zomboid/build_42_22_pre_release/ (LOW-MEDIUM)
- PZ Mapping Tools (README, docs, releases, linked world projects): https://github.com/Unjammer/PZ_Mapping_Tools (HIGH, read via GitHub API 2026-11-09)
- KnoxMap (README, `tools/make_map_mod.py`, `knoxbuild/placement.py`, `worlded/README.md`, LICENSES.md, CHANGELOG): https://github.com/spytheeuclidean-a11y/knoxmap (HIGH)
- Knoxify: https://github.com/arytek/knoxify (HIGH)
- PZ Vanilla Map B42 export: https://github.com/Unjammer/PZ_Vanilla_map_b42 (HIGH)
- Geofabrik Australia extract: https://download.geofabrik.de/australia-oceania/ (HIGH, redirect observed to `australia-261108.osm.pbf`)
- Release versions via GitHub releases API: osmium-tool v1.19.0, pyosmium v4.3.2, GDAL v3.13.3, QGIS final-3_44_15, osm2pgsql 2.3.1; Python 3.14.10 and 3.13 via endoflife.date (HIGH)
- Build 42 modding structure (`42/`, `common/`): https://projectzomboid.wiki/guides/modding-tools/ and Steam discussions (MEDIUM)
- Teleport and vehicle scripting: Steam Workshop mod threads (RV Interior B42 port, CarWanna) only. No official API doc fetched (LOW)
- Not reachable (HTTP 403/504): projectzomboid.com tools and Javadocs, pzwiki.net. Context7 required authorisation and was not used.
