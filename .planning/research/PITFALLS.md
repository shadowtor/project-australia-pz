# Domain Pitfalls

**Domain:** Real-world-geography Project Zomboid (Build 42) map mod, multi-city Australia, OSM-derived
**Researched:** 2026-11-09
**Confidence:** MEDIUM overall. Web evidence on B42 tooling is thin (42.20 released July 2026; official mapping tools were announced to follow after hotfixing and public availability was unconfirmed in sources found). Most pitfalls below are from PZ mapping community knowledge, OSM/ODbL rules and engine behaviour, and should be validated in the pilot. Items marked VERIFY need a measured check on the pinned build.

Phase names used below (suggested, roadmap may rename): **P0 Pilot/Tooling Spike**, **P1 Pipeline & Config**, **P2 Pilot Slice (Melbourne-Geelong)**, **P3 Region Production**, **P4 Corridor/Network Integration**, **P5 Release/Licensing**, **P6 Tasmania Gate**.

## Critical Pitfalls

### Pitfall 1: Tool / game / tileset version drift (B42 is a moving target)
**What goes wrong:** Map built in tools or with tile definitions from one B42 point release (e.g. 42.19) fails, renders blank/wrong tiles, or crashes on another (42.20+). Community tools (Knoxify, KnoxMap) target specific builds; official TileZed/WorldEd for B42 lagged the game. Tilesheets are partly packed inside game texture packs and must be extracted per build; mixing B41 and B42 tile defs or map folders breaks loading.
**Why it happens:** B42 unstable/stable branches change tile IDs, tilesheets, lot-pack format and world cell size (B42 cell reported as 256 tiles, B41 was 300; VERIFY). "Latest" silently moves under you via Steam auto-update.
**Consequences:** Whole-world re-export, unmatched-tile floods, saves that cannot load after a game update, "Workshop item version is different" errors.
**Prevention:** Pin game build number, tool revisions, tile-def/tilesheet extraction hash and generator commit in one `PINS` file. Disable Steam auto-update (or keep a copy of the pinned install) for the dev machine. Add a build step that fails on any unmatched tile and lists it by cell. Write the cell size and tile-ID assumptions into the P0 spike output, not from docs.
**Detection:** Pink/blank tiles, missing-tile logs, lots count mismatches after a Steam update, tool version prompts.
**Phase:** P0 (pin + measure), P1 (enforce in pipeline), re-check at every game point release (add a "re-pin" task to P3/P5).

### Pitfall 2: Treating generated output as the source of truth (regeneration clobbers hand edits)
**What goes wrong:** Regenerating from OSM/Knoxify overwrites TMX/lotheader work: hand-fixed junctions, interiors, landmarks, spawn points, zone polygons. Team stops regenerating and forks the output permanently, killing reproducibility (BUILD-01).
**Why it happens:** WorldEd/TileZed TMX files are single binary-ish blobs per cell; no merge semantics. Hand edits and generated layers share files.
**Consequences:** Lost weeks of curation; or an un-reproducible map.
**Prevention:** Strict layer ownership: generated layers (terrain, roads, water, footprints) in generated files only; hand edits in separate overlay files/layers/maps (separate TMX or object-group layers merged by script, or "stamp" files keyed by stable IDs/coordinates). Never edit a generated file by hand; CI check rejects diffs to generated paths. Add a hand-edit manifest (cell, layer, bbox) and a regen test: regenerate twice, then diff, then confirm overlays survive. Keep last-playable export as a tagged artefact before each regen.
**Detection:** Anyone saves a generated TMX directly in TileZed; regen diff touches hand-edit bboxes.
**Phase:** P1 (design overlay model before any art), proven in P2 with a deliberate regen test.

### Pitfall 3: Seam road mismatches between region exports
**What goes wrong:** Roads, lane count, road type, kerb/lane markings, shoulders, guardrails, power lines or water do not line up across cell/region edges; one side's off-by-one tile offset leaves a gap or a step. Highway "ends at a seam".
**Why it happens:** Regions generated independently with different origin transforms, rounding, or different compression ratios in the corridor; hand edits applied to one side only.
**Consequences:** Impassable road, vehicles stuck at lip, zombie/loot zone discontinuities, disconnected route graph.
**Prevention:** One global grid and one transform definition for all regions (record origin, cell offsets, projection). Define "road connection points" as data (cell, tile x/y, lane count, road tile family, Z) shared by both neighbours; generator reads them rather than deriving independently. Automated seam validator: for every shared edge compare road tiles/lane count/Z, report by region+cell. Always export and test both sides; drive across every seam both directions. Include a seam in the P2 pilot as required.
**Detection:** Validator mismatches; vehicle bounces at boundary; map viewer shows kerb mid-road.
**Phase:** P1 (connection-point schema + validator), P2 (first seam), P4 (every corridor).

### Pitfall 4: Cell count, load time and save size blowups
**What goes wrong:** Twelve cities plus thousands of km of corridor in a world grid measured in hundreds of cells makes install size, new-save load time, map-viewer memory, and per-cell chunk saves explode. Outback "empty" cells still cost lotheader/lotpack/ chunkdata disk and world-map overhead. Players' saves grow as they traverse (every visited chunk persists).
**Why it happens:** Budgets assumed, not measured; corridors and blank terrain are padded with full-detail cells; rectangular bounding box between far-apart cities wastes enormous empty cells.
**Consequences:** Multi-GB mod, minute-plus loads, stutter in vehicles, corrupt/slow saves, unshippable on low-end machines.
**Prevention:** Measure in P0 on target machine: MB per populated cell, MB per empty/water/desert cell, new-save load time vs cell count, save growth per km driven. Set hard budgets (cells, install MB, load seconds). Lay cities out in a compact world grid (do not preserve real bearings as a bounding rectangle; use route-order and topological layout) so unused ocean/desert cells are not compiled. Use vanilla-tile-only empty terrain, minimal vegetation in outback. Track the budget in CI per export.
**Detection:** Export size growth per commit; load time regression; save folder size after a 10-minute drive.
**Phase:** P0 (measure), P2 (first budget numbers), P3/P4 (gate each region on budget).

### Pitfall 5: Chunk stream-in and vehicle failures at cell boundaries
**What goes wrong:** Fast cars outrun chunk loading: player drives into unloaded squares, falls through, gets stuck, vehicle despawns or loses collision at cell boundaries, especially on high-speed straight highways and with unusual content density at the edge. Boundary bugs also from lot cell-sized objects (buildings, bridges, multi-tile props) spanning cells.
**Why it happens:** Streaming rate is bounded by disk and content density; highways at 100+ km/h in a game scaled for slower play; large static objects crossing cell edges; vehicle-in-unloaded-area save issues.
**Consequences:** Stuck/lost vehicles, crashes, corrupt vehicle state on save at a seam.
**Prevention:** Keep seams in lightly populated, simple straight sections (no bridges, junctions, buildings, Z changes on a cell edge). Make corridor tiles low-density near seams. Test at max vehicle speed both directions, with a fast and slow machine, and with save/reload while parked on and near a seam. Add a checklist item "no multi-tile object crosses a cell edge".
**Detection:** Frame hitches on crossing, "no ground" pop, vehicle stops, save/reload positions vehicle on the wrong side.
**Phase:** P2 (pilot seam is the proof), P4.

### Pitfall 6: Scale compression removes turnoffs, bridges, junction logic and sense of direction
**What goes wrong:** Compressed corridors delete intermediate junctions, service roads, rest areas and bridges, or place them out of order; sign distances stop matching drive time; player cannot find fuel; the corridor looks like a straight line with no landscape change.
**Why it happens:** Compression applied as geometric resampling of a polyline rather than curated list of controlled features; no rule for which features survive.
**Consequences:** Dead-end survival (no fuel/rest stops), nonsensical signage (e.g. "Geelong 75 km" after 5 minutes), loss of route identity, ROAD-01 failing logically even if physically connected.
**Prevention:** Corridor spec is a data file: ordered list of must-keep features (junctions, bridges, rest areas, service towns, state borders) with pinned position along the route; compression only fills between them. Sign distances derive from a single "game-km" scale agreed in P2; avoid printing real km unless scaled consistently (decide on real-km vs game-km signs early). Visual landscape-change zones (vegetation/terrain bands) defined along corridor. Compare against uniform-scale baseline in pilot (already a project decision).
**Detection:** Feature checklist vs corridor spec; signage audit; playtester asks "where do I get fuel".
**Phase:** P1 (corridor spec format), P2 (pilot Princes Fwy), P4.

### Pitfall 7: ODbL obligations misunderstood for a distributed map
**What goes wrong:** Mod ships OSM-derived geometry with no attribution, or the team assumes "baked into a game map" is a Produced Work with no obligations, or fails to publish the derived database. Share-alike applies to a derivative database; a Produced Work (rendered/compiled map) needs attribution/notice but the derivative database must be offered on request when you publicly use it.
**Why it happens:** Legal ambiguity; nobody records provenance. Compiled lotpacks may be arguably a Produced Work but the intermediate pipeline outputs (BMP/TMX) distributed anywhere are likely a derivative database.
**Consequences:** Takedown or compliance issue when publishing; inability to distribute sources.
**Prevention:** Decide posture in P0/P1: attribute "(c) OpenStreetMap contributors" visibly in-mod (mod.info description, in-game credits/sign, README, workshop page), link to openstreetmap.org/copyright and ODbL. Keep the pinned extract (date, source URL, bbox) in the repo's data folder with its own ODbL licence note, and publish the derived dataset if you share the source tree. Keep mod code licence separate from data licence. Record legal-review status; seek a quick legal check before any public Workshop release (single-player local pilot is low risk). Note: OSM-derived building footprints are fine; do not mix in non-ODbL-compatible data (Google/Bing imagery tracing, proprietary footprint datasets, Geoscape) without checking licence. Australian government open data (e.g. Geoscape, state elevation) each have own licence (CC BY variants); track separately.
**Detection:** No ATTRIBUTION file; unknown provenance of any data layer.
**Phase:** P1 (provenance schema), P5 (release gate). VERIFY with counsel; this is not legal advice.

### Pitfall 8: Redistributing third-party tools, tiles and assets
**What goes wrong:** Bundling Knoxify/KnoxMap output, other mods' tiles/tilesets, Real USA assets, vanilla PZ tilesheets/packs, or real-world sign/logo textures without rights. Vanilla tilesheets cannot be redistributed in a mod; mods may reference but not ship The Indie Stone's art. Real-brand logos (Woolworths, BP, Spirit of Tasmania ship) are trademarked.
**Why it happens:** Tools produce intermediate files containing extracted assets; repositories seldom state a licence (Knoxify/KnoxMap licences unverified).
**Consequences:** Takedowns, forced removal from Workshop, repo contamination.
**Prevention:** Asset ledger from day one (source, licence, redistributable Y/N, where used). Ship only original art + references to game tiles. For tools without a licence, treat as all-rights-reserved: use locally, do not vendor into the repo, ask the author. Generic or fictionalised brand signage (a stylised "Servo"), not trademarks, in shipped art. If any dependent mod is required, declare it in mod.info `require=` instead of bundling.
**Detection:** Files in repo without ledger entry.
**Phase:** P1 (ledger), P5 (audit).

### Pitfall 9: Ferry teleport strands players or loses save state (Tasmania)
**What goes wrong:** Teleporting a player to the far-side terminal lands them in an unloaded or non-existent cell; vehicles/occupants/cargo and trailers do not follow, are duplicated, or are lost; save during transfer leaves player on a ship cell with no return; multiplayer desyncs.
**Why it happens:** PZ teleport must wait for chunk load; vehicles are separate world objects with their own lifecycle; no official cross-map transfer API; mod scripts run client-side in SP and server-side in MP.
**Consequences:** Stranded or deleted characters and vehicles; the worst, most reputation-damaging class of bug.
**Prevention:** Keep Tasmania a late gate (already planned). Prove sequentially: pedestrian round trip with inventory and save/reload at every state; then vehicles. Teleport only after the destination square is loaded and walkable; fall back to the departure terminal with a message on failure. Persist a "ferry state" in modData so reload mid-transfer resolves to a safe terminal. Ship foot-passenger-only if vehicle path is not 100% reliable. Prefer a seamless physical ship cell adjacent to the terminal over remote teleport only if load behaviour is proven. Test on an old save, with a death/respawn during transfer, and with the game paused/quit at each step.
**Detection:** Ferry test matrix with save/reload at each step; vehicle ID and inventory hash compare before and after.
**Phase:** P6 only (gate), with the decision documented in P2 not to depend on it.

### Pitfall 10: Multi-level (Z) geometry bugs
**What goes wrong:** Overpasses, ramps, car parks, basements and Coober Pedy dugouts have vehicle-unfriendly collision (cars clip, get stuck on ramp lips), missing stair/ramp tiles, lighting and zombie pathing errors, roof/floor tile mismatches, and below-ground levels that B42 map rules or tools handle differently. Bridge decks that cross a cell seam compound it.
**Why it happens:** Vehicles use physics against floor tiles per level; the ramp/bridge tile support is limited; generated tools mostly emit Z=0.
**Consequences:** Highway bridges that cannot be driven; road network disconnected at grade-separated junctions.
**Prevention:** Default to at-grade roads: model overpasses/underpasses as at-grade or as flat crossings with a visual-only bridge unless a prototype proves a driveable bridge. Prove each Z feature type in a tiny test map in P0 (car on a ramp, up/down, save/reload on the ramp). Dugouts as pedestrian/interior-only (no vehicles). Keep Z features away from seams. Each included Z feature has a documented entrance/stair/collision test.
**Detection:** Vehicle stuck at ramp, zombies not reaching player, light leak.
**Phase:** P0 (feature proof), P3 (only proven types), P4.

## Moderate Pitfalls

### Pitfall 11: Zombie population and loot zone problems
**What goes wrong:** Real-world scale gives vast areas with no zone data: zero zombies/loot in outback, or vanilla default (Wilderness/TownZone) zoning produces wrong loot (rural gun stores in CBD), uniform density, huge zombie hordes spawned at high-density CBD cells, or spawns inside buildings/water. Building loot categories not set for generated footprints (everything becomes "residential"). Population density maps are separate files per cell that are easy to forget.
**Prevention:** Gameplay-zones layer is editable (already planned). Build per-use-class tables (CBD, suburb, roadhouse, servo, farm, outback) mapping OSM `building=*`/`amenity=*`/`shop=*` tags to room definitions and loot. Set deliberate zombie density curves per region (dense CBD, sparse outback with road-stop clusters). Play-test loot/food availability along a long leg so a driver can refuel/eat. Check spawn points are on land and outside buildings.
**Detection:** First-walk-through stats; no zombies for 20 minutes; whole town "Residential" loot.
**Phase:** P2 (pilot recipe), P3.

### Pitfall 12: Australia-specific distance and outback challenges
**What goes wrong:**
- Real distances (Adelaide-Perth ~2,700 km, Darwin-Brisbane ~3,400 km, Coober Pedy remote) are absurd; compression must also keep fuel logic coherent (vehicle fuel tank vs compressed km, which PZ models as consumption per distance driven). Fuel range must match compressed corridor so fuel stations are meaningful, not trivial.
- Nullarbor/Stuart Hwy/Great Northern are long uniform straights; boring and Z-fighting-prone terrain with no landmark; streaming still costs cells.
- Roadhouses are the only POIs; remove one and a leg is impossible.
- Coastal/ocean geometry: the map is disconnected geography (Broome/Darwin/Cairns far from others). A single connected highway network must pick a graph (e.g. Hume, Pacific, Bruce, Stuart, Great Northern, Eyre, Nullarbor) and decide the order; a topological layout may disagree with real compass bearings.
- Real Australian features: left-hand traffic (PZ vehicles drive on either side as the player chooses but AI-less roads have no lane enforcement, so signage/markings imply LHT; NPC/zombie cars do not matter), salt lakes, rivers with long bridges (e.g. Hume crossings), flood plains, roadtrain-wide roads, unsealed roads, wildlife signage, and wide dry-river crossings.
- Tropical vs arid vegetation: the vanilla tilesets lack outback/tropical (Cairns palms, mangroves) variety; faking via the vanilla set can look wrong. Check which B42 foliage tiles exist before promising Cairns/Coober Pedy identity.
**Prevention:** Define fuel/range design target (e.g. full tank to roughly the longest compressed gap without a servo) in P2; run a drive-time and fuel test per corridor. Pick the route graph and topology in P1 and record it as data. Specify one landmark/feature per N game-minutes (rest area, hill, bridge, bend, roadhouse) for every corridor so long legs are not empty. Audit the available tile vocabulary per biome before committing to a destination's identity (spike with the tile-set viewer).
**Detection:** Drive-time table against targets (5 min / 20-30 min); fuel-gauge test; "empty minutes" audit.
**Phase:** P1 (graph/topology), P2 (calibration), P4.

### Pitfall 13: OSM data quality issues become map defects
**What goes wrong:** Building footprints missing, merged or wrongly tagged; multipolygon relations break; roads with `bridge`/`tunnel`/`layer` tags rasterised flat; dual carriageways shown as single line; OSM `highway` classes do not map to lane counts (`lanes` missing); rivers/coast are inconsistently mapped; urban blocks converted to jaggy tile footprints that do not tile to PZ's 1-tile walls; building sizes generated at wrong scale produce 2x2 or 200x200 buildings.
**Prevention:** Pin the extract; filter and validate (area limits, min/max building size, self-intersection repair) in a normalisation step; log skipped features. Rasterisation rule table for lanes per highway class with an override file. Do not auto-generate hero buildings/landmarks: hand-author these in overlays. Footprints are inputs only; walls, doors, interiors are designed templates.
**Detection:** Footprint rejects report; tile-count anomalies.
**Phase:** P1.

### Pitfall 14: Coordinate/projection and scale drift across regions
**What goes wrong:** Mixed projections (Web Mercator vs local UTM zones), different metre-per-tile values for city vs corridor, rounding differences cause cumulative drift; Australian cities span multiple UTM zones; Web Mercator exaggerates Darwin/Melbourne differently.
**Prevention:** One documented projection per city (local metric, e.g. GDA2020 MGA zone) plus a named transform to the global game grid; store tile-per-metre as config per region and the blend function in the corridor. Record all in `PINS`/config. Unit-test transforms with known landmarks.
**Phase:** P1.

### Pitfall 15: Failed or partial builds overwrite the last playable export
**What goes wrong:** Compile failure leaves a half-written mod directory that the game then loads, so crash/ black screen.
**Prevention:** Build into a staging directory; atomically swap only after validation (seam validator, unmatched tiles, route connectivity); keep N prior exports. Matches the brief's error-handling strategy.
**Phase:** P1.

### Pitfall 16: Local-install fragility (mod.info, map folder layout, spawn regions)
**What goes wrong:** Map does not appear in the new-game map selection because of wrong `media/maps/<name>` layout, missing `map.info`, `spawnpoints.lua`, `spawnregions.lua`, B42-specific `42/` versioned mod folder, wrong `id`, or conflicting with vanilla Muldraugh region. Players load with Muldraugh map and the Australian map overlays on top, mixing worlds.
**Prevention:** Follow the pinned build's official mod-structure documentation (B42 requires versioned `42/` directory structure; VERIFY). Test a clean install from the documented steps on a fresh profile as an acceptance test (already in the brief). Make the map standalone (do not load vanilla Muldraugh cells in the world); set `lots`, spawn regions and the world-map (in-game map) data explicitly.
**Phase:** P0/P2.

### Pitfall 17: In-game map and navigation not generated
**What goes wrong:** The in-game map (M key) is blank or shows the vanilla US map because world map XML/images and symbols are not provided; signs are decorative tiles with no readable text; players cannot navigate 100s of km.
**Prevention:** Make in-game map data and street-label/world-map generation a P2 deliverable, not a polish item. Sign readability test at driving speed. Consider a mod-provided map overlay as an additional navigation aid. VERIFY B42 map-data format on the pinned build.
**Phase:** P2.

## Minor Pitfalls

### Pitfall 18: Map viewer or map-editor limits as bottleneck
**What goes wrong:** TileZed/WorldEd become unusably slow or crash on large worlds; one TMX per cell inflates repo size.
**Prevention:** Work region-by-region; store large binaries in Git LFS or exclude generated outputs and regenerate from config.
**Phase:** P1.

### Pitfall 19: Multiplayer assumptions creep in
**What goes wrong:** Scripts written client-side only, mod data not server-safe; large mod fails to sync on server.
**Prevention:** Explicitly SP-only for v1; note any server-unsafe scripting; defer MP tests to a later decision.
**Phase:** Out of scope; flag in P5.

### Pitfall 20: Not counting performance of vehicles over time
**What goes wrong:** Frame-rate drops with high vehicle spawn density along roads or long drives with many wrecks; vehicle spawn zones not set on generated roads, so no cars exist.
**Prevention:** Define vehicle-spawn zones per road class and per city; test finding a vehicle on foot within N minutes of spawn.
**Phase:** P2/P3.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| P0 Tooling spike | Version drift (1), Z feature feasibility (10), cell cost (4), install layout (16) | Pin build; tiny test map with ramp, seam, empty cells; measure MB and load |
| P1 Pipeline/config | Clobbered edits (2), seam schema (3), projection (14), OSM quality (13), provenance (7, 8), staging builds (15) | Overlay model, connection-point schema, ledger, atomic export |
| P2 Pilot slice | Seam streaming (5), compression (6), loot/zombies (11), nav/map (17), fuel/scale (12) | Drive both ways, budget table, regen test, clean install test |
| P3 Region production | Budget creep (4), identity vs tile vocabulary (12), zone tables (11) | Per-region budget gate, identity checklist, hand overlays |
| P4 Corridor integration | Seams (3), feature survival (6), long-leg emptiness (12) | Seam validator in CI, feature list, drive every link both ways |
| P5 Release | ODbL attribution (7), asset redistribution (8), game point-release drift (1) | Ledger audit, re-pin, clean-install acceptance |
| P6 Tasmania | Ferry stranding (9), vehicle transfer, Z ship geometry (10) | Pedestrian-first, save/reload matrix, foot-passenger fallback |

## Research Flags
- Needs deeper phase research: P0 (pinned-build mapping tool state, cell size, mod folder layout, world-map format), P6 (ferry/teleport mechanics and vehicle transfer), ODbL posture (legal review), Knoxify/KnoxMap licences.
- Standard patterns, less research: Seam validator, atomic export, ledger.

## Sources
- Project Zomboid 42.20 release and stable plans posts (projectzomboid.com/blog/news/2026/07/) - mapping tools announced to follow; MEDIUM
- PZ B42.19 maps index (pzfans.com) - B42 cell size 256x256 listed; MEDIUM, VERIFY
- Unjammer/PZ_Vanilla_map_b42 (GitHub) - tilesheets need extraction from texture packs; MEDIUM
- Steam Workshop comments on map/game build matching and B41/B42 separation; LOW-MEDIUM
- OpenStreetMap copyright and ODbL: https://www.openstreetmap.org/copyright and OSM Foundation Collective/Produced Work guidelines (training knowledge, not re-fetched this session); MEDIUM
- Knoxify/KnoxMap repos (fetch failed this session; licence and limits unverified): LOW
- Domain/engine behaviour claims (streaming, vehicle physics, teleport, Z collision) from training knowledge of PZ modding, not verified on B42: LOW-MEDIUM, must be proven in P0
