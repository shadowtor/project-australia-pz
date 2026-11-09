# Architecture Patterns

**Domain:** Generated-plus-hand-edited Project Zomboid (Build 42) multi-city map mod (real Australia, compressed highways)
**Researched:** 2026-11-09
**Overall confidence:** MEDIUM (pipeline shape and PZ file/grid facts are well established; Knoxify/KnoxMap details verified from their READMEs; B42-specific compiler behaviour, ferry/vehicle transfer and multi-region merge are unproven and need pilot measurement)

## Recommended Architecture

Opinion: build this as a **one-way, layered, content-addressed build** (`sources -> derived -> composed -> compiled -> installed`) driven by plain Python scripts and a single `make`-style task runner. Generated output is never edited. Hand work lives in a separate overlay tree that is applied on top of generated output at a defined merge point. WorldEd/TileZed remain the **authoring and compile tools**, not the source of truth for generated geography.

Reference points: Knoxify (OSM -> three palette-exact BMPs `<map>.bmp`, `_veg.bmp`, `_ZombieSpawnMap.bmp`, rounded to the 300x300 cell grid, writes source metadata) and KnoxMap (Python, area -> terrain -> buildings -> compile -> install, uses PZ_Mapping_Tools + a patched WorldEd compiler, rebuild reuses saved map data, OSM/hand-drawn data win). Neither is a multi-region national pipeline; treat them as **stage implementations to evaluate and wrap**, not as the architecture. KnoxMap's own docs state multi-mod area overlap conflicts and MP is untested.

```
                 (pinned, read-only)                (small, human-owned, versioned)
  +-------------------------+        +----------------------------------------------+
  | 1. SOURCE SNAPSHOT      |        | 2. DESIGN CONFIG                             |
  |  OSM extract(.pbf)+hash |        |  route graph (nodes/edges, junction IDs)     |
  |  DEM/landcover (opt)    |        |  scale profile per segment (city/corridor)   |
  |  tool/game/version pins |        |  world grid + region/cell allocation         |
  +-----------+-------------+        |  stop/landmark manifest                      |
              |                      +----------------------+-----------------------+
              v                                             |
  +---------------------------------------------------------v--------+
  | 3. GEO-PROCESSING (deterministic)                                 |
  |  clip -> project (one CRS) -> per-segment scale transform         |
  |  -> corridor synthesis (compressed polylines) -> city extracts    |
  |  -> blend zones (outskirts) -> "world-space vector model" (GeoJSON|GPKG)
  +-----------------------------+------------------------------------+
                                v
  +-----------------------------------------------------------------+
  | 4. RASTER GEN: per-cell/per-region BMPs (terrain, veg, spawn)   |
  |    + building footprint sets + map-budget report                |
  +-----------------------------+-----------------------------------+
                                v   generated/ (disposable, hash-stamped)
  +-----------------------------------------------------------------+     +-----------------------+
  | 5. COMPOSE: generated layer  (+ overlay precedence)  <-----------------+ 6. HAND-EDIT OVERLAYS |
  |    -> WorldEd world (.pzw) + per-cell .tmx + lots/buildings    |     |  per-cell TMX/tbx     |
  +-----------------------------+-----------------------------------+     |  patch rasters/masks  |
                                v                                         |  locked-feature list  |
  +-----------------------------------------------------------------+     |  Lua/script mods      |
  | 7. COMPILE (WorldEd/PZ tools) -> lotheader/lotpack/chunkdata   |     +-----------------------+
  |    + worldmap xml + spawnpoints + map.info (mod payload)        |
  +-----------------------------+-----------------------------------+
                                v   (atomic, versioned releases/)
  +-----------------------------------------------------------------+
  | 8. INSTALL to game mods dir (junction/copy) + 9. VALIDATION     |
  |    static gates (graph, seams, budgets) -> in-game smoke tests  |
  +-----------------------------------------------------------------+
        Ferry prototype (separate mod, 10) plugs in only at 5/7 as a pair of terminal cells
```

### Repository / directory layout (the "stay separate" contract)

```
sources/            # READ-ONLY. pinned inputs; manifest.json with sha256, date, URL, licence
  osm/australia-YYYYMMDD.osm.pbf  (or regional clips)
  manifest.json
config/             # human-authored, small, diffable, versioned
  world.yaml        # CRS, origin, cell size (300), region->cell-rect allocation, tool/game pins
  routes.yaml       # route graph: nodes (cities, junctions, stops), edges (highway ref, order, bearing)
  scale.yaml        # profiles: city=1.0 m/tile, corridor=k:1 compression per edge, blend length
  stops.yaml        # roadhouses, fuel, rest areas: id, anchor node, template
edits/              # HAND WORK. never overwritten by generators
  <region>/<cx>_<cy>/ ...        # per-cell TMX / building (.tbx) / lot overrides
  masks/<region>/*.png           # paint-over masks: "keep road here", "force water"
  features/*.yaml                # curated features keyed by STABLE ID (see below)
  lua/                           # media/lua gameplay (ferry, spawns, signs)
generated/          # DISPOSABLE. rm -rf safe. every file stamped with input hash
  <region>/rasters/*.bmp, footprints.geojson, report.json
  world/*.pzw, <cell>.tmx
build/ releases/    # compile output; releases/<ver>/ immutable; `current` points to last GOOD
tools/              # wrappers + pinned versions of Knoxify/KnoxMap/PZ_Mapping_Tools/WorldEd (submodule or lockfile)
validate/           # graph, seam, budget checks; fixtures
```

Rule: **a tool may only write inside its own output directory, and may read only from directories to its left in the diagram.** `edits/` is never an output of any tool except an explicit "promote" command run by a human.

## Component Boundaries

| # | Component | Responsibility | Reads | Writes | Talks to |
|---|-----------|---------------|-------|--------|----------|
| 1 | Source snapshot | Pin OSM extract, DEM, landcover; record date/hash/licence | network once | `sources/` + manifest | 3 only |
| 2 | Design config | Route graph, scale profiles, grid/region allocation, stop manifest, tool pins | human | `config/` | 3, 5, 9 |
| 3 | Geo-processing | Clip, project, scale-transform, synthesise corridors, blend zones, emit one world-space vector model | 1, 2 | `generated/model/` | 4, 9 |
| 4 | Raster/footprint generator | Rasterise per cell to palette-exact BMPs; building footprints; spawn density; budget report | 3 | `generated/<region>/` | 5 |
| 5 | Composer | Build WorldEd world + per-cell TMX from BMPs; apply overlay precedence; register lots | 4, 6, 2 | `generated/world/` | 7 |
| 6 | Hand-edit overlays | Curated roads, buildings, landmarks, masks, gameplay zones, Lua | human (TileZed/WorldEd/BuildingEd) | `edits/` | 5, 7 |
| 7 | Compiler | Run pinned WorldEd/TileZed batch compile; produce lotpack/lotheader/chunkdata, worldmap data | 5 | `build/` | 8 |
| 8 | Installer + release store | Atomic publish to `releases/<ver>`, copy/junction into game mods dir, keep last-good | 7 | `releases/`, game dir | 9 |
| 9 | Validation | Static gates (graph, seams, budget, palette, licence) and in-game smoke scripts | 2, 3, 4, 7, 8 | `validate/reports/` | gates 5/7/8 |
| 10 | Ferry prototype | Standalone test mod: two terminal cells + Lua transfer + safe fallback | own config | own mod | merged to main only after gate |

Component 3 is the **only place that knows about geography and scale**; everything downstream operates on tiles. Component 5 is the **only place that merges generated and hand work**. Keeping those two single-owner is what makes regeneration safe.

## Data Flow

Direction is strictly left-to-right / top-to-bottom. No downstream edit flows upstream; instead a human edit is captured as an overlay (6) or a config change (2).

1. **Pin.** Download once; record sha256, extract date, ODbL attribution string. All later stages take the manifest hash as input.
2. **Configure.** `routes.yaml` defines the national graph with stable node IDs (e.g. `MEL`, `GEE`, `J_PRINCES_WERRIBEE`, `STOP_LARA_RESTAREA`). `scale.yaml` assigns a profile per node (city, 1 m/tile) and per edge (corridor compression ratio, blend length in tiles). `world.yaml` allocates every node and edge to a cell rectangle on the **single global grid**.
3. **Transform.** For each edge, take the real highway polyline, resample it to the compressed length, preserve bearings at endpoints and at named junctions, keep turn-off/bridge/stop anchors as *pinned vertices that compression may not delete*. For each city, clip the OSM extract and rotate/translate (KnoxMap rotates to the street grid; for a *continuous* world that rotation must be recorded and the corridor end must match it).
4. **Blend.** Over a configured outskirts length (start ~1-2 cells; decide in pilot), interpolate scale from corridor ratio to 1:1 so the highway enters the local street network without a kink. Emit the blended polyline as a first-class road in the vector model, not as a patch.
5. **Rasterise.** Cut the global vector model on 300x300 tile boundaries (cell = tile origin multiples of 300), emit BMPs per region. Every pixel from the PZ palette; unknown colours are a build failure.
6. **Compose.** Create the WorldEd world with each region's BMP placed at its global cell offset; run BMP->TMX; then apply overlays in precedence order: generated < overlay masks < per-cell TMX/tbx edits < locked features. Output `.pzw` + TMX.
7. **Compile.** Batch compile to lot data into `build/`. Only on success is a new `releases/<ver>/` created and `current` repointed. A failed compile leaves `current` untouched (satisfies "preserve last playable export").
8. **Validate and install.** Static gates first (cheap), then install, then scripted in-game checks.

### Combining cells, WorldEd worlds and multi-region exports on one grid

- **Cell = 300x300 tiles** (PZ map cell; Knoxify rounds output to this grid). The world is an integer grid of cells `(cx, cy)`. World tile coordinates are `x = cx*300 + lx`. Treat `(cx, cy)` as the primary key for everything: rasters, TMX, lots, validation reports, edits directories.
- **One global grid, many regions.** "Region" (Victoria, NSW/ACT, QLD, NT, WA, SA, plus corridors) is an *organisational unit* for export/test, not a coordinate system. Each region owns a **disjoint cell rectangle** in `world.yaml`. No region has its own origin. Regions that share a seam share an edge of cells; the seam cell pair is defined once in `routes.yaml` (edge crosses cell boundary at tile row/col N with road width W).
- **Allocation strategy.** Lay out the national topology as an abstract compressed grid first (cities in roughly correct bearing and order, corridor lengths from drive-time targets), assign cell rectangles, and leave **gap cells (void/ocean/bush) rather than packing tightly**, so a later corridor extension doesn't force a renumber. Renumbering cells invalidates every hand edit keyed by `(cx,cy)`. Treat `world.yaml` allocation as append-mostly after pilot.
- **Single WorldEd world vs per-region worlds.** Recommend ONE `.pzw` world file with sub-maps placed by cell offset, and per-region *compile profiles* (a subset of cells) for fast iteration. Per-region compile is a build-time convenience; the shipped mod is the union. If WorldEd/compiler memory or time makes the union impractical, fall back to several map directories in one mod (PZ supports multiple map folders listed in `map.info`/mod `maps=`; MEDIUM confidence) sharing the same global coordinates. Decide with a measured pilot, not up-front.
- **Cell budget is a first-class output.** Component 4 emits per-cell and total counts (non-empty cells, estimated lot size). Empty/ocean cells cost little; dense city cells cost most. Corridors are cheap if mostly terrain. Gate on the budget in `world.yaml`.
- **Conflicts.** Other map mods occupying the same coordinates conflict (KnoxMap warns of this). Choose a cell range far from vanilla Knox County and document it; spawn selection must be compatible with that.

### Hand-edit preservation (regeneration safe)

Three mechanisms, use all three:

1. **Physical separation.** `generated/` is disposable; `edits/` is hand-owned. Regeneration only ever deletes `generated/`.
2. **Stable feature IDs.** Every curated thing (a landmark, building, junction, stop) gets an ID in `edits/features/*.yaml` that references a **config anchor** (node ID + offset in tiles, or OSM way ID + hash of geometry) not an absolute tile coordinate. After regeneration the composer re-resolves anchors; if an anchor moved more than a tolerance or its source way vanished, it reports an **orphaned edit** rather than silently dropping or misplacing it.
3. **Overlay precedence + locks.** Per cell: `generated < mask patches < hand TMX layers < locked`. A hand-edited cell can be marked `lock: true`, in which case the composer takes its TMX verbatim and only the *seam rows/cols* are re-checked against neighbours. Edits to buildings go in BuildingEd `.tbx`/lot overrides, never into generated TMX.

Practical rule for authors: in TileZed/WorldEd, edit only on **dedicated overlay layers/files** (e.g. extra tile layers or a separate TMX per cell committed under `edits/`); never "Save" over a generated TMX. Provide a `promote` script that moves a hand-modified generated cell into `edits/` so it cannot be clobbered. TMX/BMP are binary-ish, so diff via exported PNG + layer-hash in CI; keep `edits/` in git (LFS if large).

### Compressed highway corridors blended into playable-scale cities

Model the national map as a **graph of two kinds of edges and nodes** with a scale function:

- **Node types:** `city` (scale 1:1, rendered from OSM extract), `junction` (scale-locked pocket, e.g. 1:1 around an interchange so ramps/lanes are playable), `stop` (roadhouse/fuel/rest area, 1:1 template), `seam` (cell boundary pin).
- **Edge type:** `corridor` with `real_length_m`, `target_tiles`, `compression = real/target`, and a list of **pinned anchors** (junction/stop/bridge/turn-off positions given as fractions along the real route). Compression is a *monotone remap of arc-length*: `s_game = f(s_real)` where `f` is piecewise linear, slope 1 inside pinned pockets and slope `1/k` between them. This guarantees stops and junctions survive compression and keeps them at the correct order.
- **Blend:** within `blend_len` tiles of a city outskirts, slope ramps from `1/k` to 1 (smoothstep on arc-length) and lateral features (land use, density, vegetation) interpolate between the corridor's landscape type and the city's. Roads must be one continuous polyline across the blend; do not stitch two separate generations.
- **Landscape strips:** corridor terrain comes from low-res land cover (bush, farm, desert, tropical) along the polyline, drawn as a swath of width W cells either side of the road, with biome keyed per edge segment. This is where the "landscape changes" requirement is delivered.
- **Parameters for the pilot:** log `target_tiles`, measured drive time (vanilla car speeds), compression ratio, and share of settlement represented; compare with a uniform-scale baseline generated from the same pipeline by changing only `scale.yaml`. This is the payoff of keeping scale in config: **scale is one file, rerun the pipeline**.
- **Constraint:** keep road class (freeway, dual carriageway, single lane) and lane count constant along the edge; only length changes, never width. Compress length, never cross-section.

### Automatic validation

Run as a pipeline stage between each pair of steps; non-zero exit blocks promotion. All checks read the world-space vector model and/or the final rasters (road pixels / tile layers).

| Check | Method | Fails when |
|-------|--------|-----------|
| Route-graph connectivity (design) | Load `routes.yaml`; union-find over mainland nodes; assert one component containing all 12 destinations; every pair reachable | Any destination isolated; edge references missing node |
| Route-graph connectivity (as built) | Extract road tiles from final layers (road/asphalt tile classes), flood-fill/skeletonise into a graph; map each design node to a tile region; assert a path exists per edge and per destination pair; report by region and cell | A design edge has no built path; road ends in non-road tile |
| Dead ends / seam stubs | For every cell pair sharing an edge, compare road-tile run positions and widths on the last row/col of A with the first of B; also check class (lane marking) | Run present on one side only, offset > 0 tiles, width mismatch |
| Cell seam terrain continuity | Compare edge-row palette of terrain/veg/water across seam; flag discontinuity beyond tolerance (e.g. water vs grass) | Coastline or river breaks at seam |
| Compression integrity | Assert every pinned anchor survives, arc-order preserved, bearing deviation < tolerance at nodes | Missing junction/stop/bridge; reordered junctions |
| Slope/kink at blend | Max curvature and width continuity across blend zone | Kink > threshold |
| Palette/format | BMP pixel values subset of PZ palette; size multiple of 300 | Unknown colour; wrong dimensions |
| Budget | Count non-empty cells, estimated size; compare with `world.yaml` limits | Over budget |
| Orphaned edits | Re-resolve anchors | Anchor not found / moved beyond tolerance |
| Licence/attribution | Manifest lists OSM + third-party assets; attribution file present in mod | Missing credit |
| In-game smoke (scripted + manual) | Teleport/debug-mode vehicle along each corridor both ways via a Lua test harness recording position/stream-in errors; save/reload mid-corridor | Vehicle stuck, void tile, console errors |

In-game checks are partly manual in PZ (no headless server for single-player); a debug Lua mod that drives a vehicle along a stored polyline and logs the console is the best automation lever (LOW-MEDIUM confidence; prove in pilot). Static gates cover most seam failures cheaply.

### Bass Strait ferry as a separate prototype

- **Separate mod, separate repo directory, separate gate.** `ferry-proto/` is its own tiny map+Lua mod with two small terminal cells (departure at Geelong, arrival at Devonport) and a static ship interior cell. It uses the same `world.yaml` grid conventions so the cells can later be *merged* but depends on nothing from the mainland pipeline except the terminal cell template.
- **Mechanism:** a world interaction (context menu on a boarding-point object, or a trigger zone) runs a Lua transfer: validate destination cell is loaded and arrival square is safe, then teleport the player (and later the vehicle) to arrival; on failure, leave the player at the departure terminal and show the message.
- **Proof ladder (each rung a gate):** (1) pedestrian round trip with inventory and save intact; (2) same after save/reload at each side and while "aboard"; (3) vehicle transfer with driver; (4) occupants and cargo; (5) failure injection (destination cell unloadable, blocked arrival square). Stop at the first failing rung and ship the highest-passing rung (foot-passenger is the acceptable fallback). Vehicle teleportation in PZ is the riskiest unknown (LOW confidence; needs in-game proof, and B42 vehicle API may differ from B41).
- **Integration:** Tasmania adds a second landmass region to `world.yaml` far from the mainland (distinct cell rectangle; no physical road link, which the design explicitly allows). `routes.yaml` marks the ferry edge `type: scripted` so the connectivity check treats it as a separate component link and the mainland check ignores it (mainland must be connected without it).
- **Why late:** it adds no dependency to mainland phases, and the mainland pipeline does not change if the prototype fails.

## Patterns to Follow

### Pattern 1: Config-as-source, outputs-as-cache
**What:** Scale, routes and grid live in small YAML; every generated artefact records the hash of its inputs and tool versions. A stage skips if the hash matches.
**When:** Always. Enables the drive-time vs uniform-baseline comparison by changing one file.
**Example:**
```python
# stage = pure function of (inputs, config slice, tool_version) -> outputs
key = sha256(sources_hash, cfg_slice_json, TOOL_VERSION)
if (out / ".key").read_text() == key: return  # cached
```

### Pattern 2: Anchor-based curated features
**What:** Hand edits reference stable anchors (node ID + tile offset), not absolute coordinates.
**When:** Any edit that must survive a regeneration with moved geometry.

### Pattern 3: Atomic release with last-known-good
**What:** Compile into `build/tmp`, validate, rename to `releases/<ver>`, repoint `current`. Installer always installs `current`.
**When:** Always; this is the "preserve last playable export" requirement.

### Pattern 4: Stage gates fail loud, report by region and cell
**What:** Every validator prints `region/cx_cy` plus tile coordinates for each failure and writes a JSON report, matching the error-handling strategy in the brief.

### Pattern 5: Region compile profiles
**What:** Compile and test subsets (`--cells 12..15,8..9`) for iteration; full union compile at release gates only.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Editing generated TMX/BMP in place
**What:** Opening the generated world in WorldEd and saving over it.
**Why bad:** Next regeneration destroys it; no way to tell what was hand-made.
**Instead:** Edit only overlay files under `edits/`; `promote` command to adopt a cell.

### Anti-Pattern 2: Per-region origins / local coordinates
**What:** Each region generated with its own (0,0) and shifted at the end.
**Why bad:** Seam mismatches, off-by-N-cell errors, hand edits keyed to shifting coordinates.
**Instead:** One global CRS->tile transform recorded in `world.yaml`; regions are cell rectangles.

### Anti-Pattern 3: Stitching corridor and city as separate generations
**What:** Generate each city and each corridor independently and join at the boundary.
**Why bad:** Road kinks, width/lane mismatch, duplicated or missing ramps.
**Instead:** Build one continuous road polyline (with scale function) and cut cells from it.

### Anti-Pattern 4: Uniform compression that deletes anchors
**What:** Scaling the whole route by a constant factor.
**Why bad:** Removes turnoffs, bridges and service stops (named risk in the brief); makes city streets unplayable.
**Instead:** Piecewise arc-length remap with scale-locked pockets around pinned anchors.

### Anti-Pattern 5: Live data pulls in the build
**What:** Overpass queries during generation.
**Why bad:** Non-reproducible, rate-limited, data drifts. (Knoxify caches Overpass by default; pin a Geofabrik/Planet extract and disable network in the build.)
**Instead:** Pinned `.pbf` + `osmium`/pyosmium clips from the snapshot.

### Anti-Pattern 6: Treating compile or editor preview as done
**What:** Declaring success on a clean WorldEd compile.
**Why bad:** Brief defines completion as install + in-game test.
**Instead:** Smoke pass on the deployed build (test branch/environment) per phase; full corridor drive tests at release gates.

### Anti-Pattern 7: Building ferry into the mainland critical path
**What:** Making Tasmania cells part of the first world grid and compile.
**Why bad:** A failed ferry blocks mainland.
**Instead:** Separate mod, separate gate, reserved-but-empty cell rectangle.

## Suggested Build Order (dependencies drive phases)

1. **Foundations / pins** (blocks all): choose and pin Build 42 release, WorldEd/TileZed, PZ_Mapping_Tools, Knoxify/KnoxMap revision; record CRS, grid, cell size; create repo layout, manifest, licence ledger. Prove the toolchain end to end on a tiny map (one cell) -> installed -> loads in game. *This answers "which tools" and is a research flag.*
2. **Route graph + scale config (design-time)**: author `routes.yaml`, `world.yaml` allocation, `scale.yaml`; implement static connectivity check on the design graph. Cheap, no game needed; validates the whole mainland topology early (brief: "lay out the national route graph early").
3. **Pilot vertical slice (Melbourne district + Geelong district + Princes Freeway corridor)**: implement stages 3-8 minimally; one junction, one stop, one seam; measure drive time, cell count, load time. Run uniform-scale baseline by changing config only. **Output: decision on tools, scale ratio, blend length, quality bar, budgets.**
4. **Overlay/regeneration safety**: add `edits/`, anchor resolution, `promote`, locks, orphan report; prove by regenerating the pilot and confirming a hand-edited building/road survives. Do this *before* scaling production, since every later hand edit depends on it.
5. **Validation suite hardening**: built-graph connectivity from compiled tiles, seam comparator, budget and palette gates, in-game drive harness. Wire as gates to each release.
6. **Regional production (repeat per region, in route order)**: SA/Vic/NSW-ACT/QLD/NT/WA, adding cities and corridors incrementally on the same grid; each region ends with a seam test against already-built neighbours and a two-way drive. Order by chain adjacency so every increment keeps one connected graph (e.g. MEL-GEE -> Adelaide -> ... or MEL -> Canberra -> Sydney -> Brisbane...), outlier/hard cities (Coober Pedy dugout Z-levels, Cairns, Darwin, Broome) later.
7. **Selective Z-level/overpass features**: only after the base pipeline is stable; each tested on foot/vehicle.
8. **Full-mainland integration + release gate**: union compile, full corridor drive matrix, budgets, licence audit, clean-install test.
9. **Ferry prototype (can run in parallel from step 3 onward as an isolated mod, but gated late)**: pedestrian -> vehicle -> failure modes; merge into main only if passes. Reserve Tasmania cell rectangle in step 2.

Dependencies: 1 -> everything; 2 -> 3 -> 4 -> 5 -> 6 -> 8; 7 depends on 6 for the relevant region; 9 depends on 1 and 2 only (but integration depends on 8).

## Scalability Considerations

| Concern | Pilot (2 districts + corridor) | Mainland (12 cities + corridors) | Notes |
|---------|-------------------------------|----------------------------------|-------|
| Cell count | tens of cells | hundreds to low thousands (mostly low-cost terrain cells) | Measure; budget in `world.yaml` |
| Compile time | minutes | long; use per-region compile profiles and caching | Keep per-cell hash cache |
| Raster size | small BMPs | large; generate per region, not one monolithic BMP | Memory: tile windows |
| Hand edits | few | many; need anchors + locks to stay manageable | Git for `edits/` |
| Validation | in-game manual | automate static; scripted drive test; manual only for feel | Cheap gates first |
| Install size / load time | measure | measure on target machine; may force corridor compression or fewer city cells | Set budgets after pilot |

## Open Items for Phase-Level Research

- **Compiler behaviour in B42** (WorldEd batch compile, lotpack format, per-chunk limits): needs a hands-on spike in the foundations phase. LOW-MEDIUM confidence on exact file set.
- **Multi-region union vs multiple map folders** in one mod: decide by measurement in pilot.
- **Vehicle transfer for the ferry** and save/reload behaviour: LOW confidence, needs in-game proof; plan for foot-passenger fallback.
- **In-game map (worldmap xml) generation** for a compressed, multi-region world: confirm KnoxMap's output handles non-contiguous regions; MEDIUM.
- **Whether KnoxMap/Knoxify can be wrapped** (non-GUI/CLI mode, accept a pre-warped vector model) or whether only their raster conventions should be reimplemented. KnoxMap rotates cities to the street grid and fits buildings automatically; the national pipeline needs those transforms recorded and invertible. Evaluate in foundations.
- **ODbL derived-database obligations** for a distributed map built from OSM: legal check; record in licence ledger.

## Sources

- Knoxify README (raw.githubusercontent.com/arytek/knoxify): OSM -> three BMPs, 300x300 cell rounding, scale options, Geofabrik pack/Overpass cache, no building generation (HIGH for this tool's behaviour)
- KnoxMap README (raw.githubusercontent.com/spytheeuclidean-a11y/knoxmap): choose area -> terrain -> buildings -> compile -> install, B42-only, patched WorldEd compiler, rebuild reuses saved data, overlapping map-mod conflicts, MP untested (HIGH for this tool's behaviour)
- Project brief and PROJECT.md in this repo (HIGH for requirements)
- PZ cell size and file layout, multi-map-folder mods: training knowledge, not re-verified this session (MEDIUM)
- Ferry/vehicle teleport behaviour in B42: no source verified (LOW)
