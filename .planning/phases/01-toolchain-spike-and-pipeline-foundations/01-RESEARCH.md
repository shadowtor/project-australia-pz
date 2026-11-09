# Phase 1: Toolchain Spike and Pipeline Foundations - Research

**Researched:** 2026-11-09
**Domain:** Project Zomboid Build 42 map toolchain pinning, edit-safe build pipeline, in-game engine proofs
**Confidence:** MEDIUM (tool pins, hashes, vanilla file facts and licence texts HIGH; KnoxMap headless flow and in-game behaviour MEDIUM/LOW)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Tiered proof for ramps/overpass, basement entrance and ferry-style teleport. Each feature needs 3 consecutive passes in one session, then one save / quit-to-menu / reload where it must still work. The user plays and reports; the AI cannot run Zomboid.
- **D-02:** Verdicts: PROVEN only if every required trial passes (one failure = INCONCLUSIVE). RULED OUT only after two independent attempts with different implementations fail the same way, with a logged cause (console.txt or visible symptom) and a plausible engine-level reason.
- **D-03:** Per-trial protocol. Ramp: drive both directions, 3x each, park mid-structure, save/reload, drive off. Basement: walk in/out 3x, reload while inside and outside. Ferry: A→B→A 3x on foot and with a vehicle, save at B, reload, return; no duplicated/vanished zombies or items.
- **D-04:** Evidence per feature in `.planning` checklist and the Phase 1 decision file: build 42.21, mod version, date, per-trial pass/fail, reload result, console errors, one screenshot per result, verdict line (PROVEN / RULED OUT / INCONCLUSIVE + next step).
- **D-05:** The developer's Windows 11 Pro machine is the single reference machine; record CPU, GPU, RAM, SSD. A minimum-spec note is a later sanity check, not a Phase 1 gate.
- **D-06:** Measure first, then freeze. Record vanilla Muldraugh (and Real USA if installed) on the same machine for MB per populated/empty cell, new-save load time and driving FPS/stream-in; 3 runs, median. Then measure the pilot cell.
- **D-07:** Freeze budgets at spike end as ceilings relative to vanilla into one budgets file read by the BUILD-03 gates. Starting guess: pilot MB/cell no more than ~1.5x vanilla (unconfirmed, to be confirmed with user when frozen); fixed load-time ceiling. Export-size ceiling = cell count x MB/cell (populated vs empty) at the recorded cell format. Re-derive if build or cell format changes. Reversibility: reversible (a config file).
- **D-08:** KnoxMap is used first to get a loading B42 cell fast. Pin its release tag and the patched `PZWorldEd_cli.exe` SHA-256 in PINS, `auto_update` off, Geofabrik extract pinned and checksummed (no Overpass/live pull). Phase 1 proves repeat builds through this pinned KnoxMap path. Reversibility: costly (KnoxMap authors in 300-tile cells and its output conventions may shape the cell-size decision and early config).
- **D-09:** An own Python generator (pyosmium on the pinned extract, PZ Mapping Tools 43.00B261030) is built in Phase 2, replacing KnoxMap before corridor work. Do not let KnoxMap become the production pipeline.
- **D-10:** Licence handling: never copy Knoxify-derived files (no licence published, all rights reserved per KnoxMap LICENSES.md). KnoxMap's patched `worlded/` and prebuilt CLI are GPL-2.0-or-later; run unmodified as an external tool, and ship source if ever redistributed. The BUILD-05 ledger gets rows for ODbL (OSM), GPL-2.0+ CLI, and "not copied, licence unpublished" for Knoxify.
- **D-11:** PINS locks: PZ 42.21 Stable (recheck 42.22 before final pin), PZ Mapping Tools zip + SHA-256, KnoxMap release tag + CLI hash + LICENSES.md hash, Python 3.13 + lockfile (for tooling), Geofabrik extract URL/date/SHA-256, generator commit when it exists.
- **D-12:** Hybrid model following planned precedence (generated < masks < hand TMX < locked). Discrete features anchor to stable IDs (OSM way/node id or deterministic generated ID + geometry hash + tile offset) in `edits/features/*.yaml`. Freeform painting goes in per-cell overlay TMX layers with a drift check. Whole-cell lock via `locks.yaml` is the escape hatch. Reversibility: costly.
- **D-13:** Edits enter `edits/` only through an explicit human `promote` command, which records cell, layers touched, resolved anchors and a hash of the generated tiles overlaid.
- **D-14:** Orphans are never silently dropped or placed: kept in `edits/`, excluded from composed output until re-anchored. Report is `orphans.json` plus console table (`edit_id`, `kind`, `anchor`, `reason` = missing_source | moved_beyond_tolerance | hash_mismatch, last-known cell/tile, file), summary `N edits: X survived, Y moved within tolerance, Z orphaned`; non-zero exit with `--strict`.
- **D-15:** Regen test: snapshot `edits/` hashes, delete `generated/`, regenerate, compose, assert every edit present and `edits/` hashes unchanged; then perturb inputs (remove one way, shift one node past tolerance) and assert exactly those edits orphan and nothing else changes.

### Claude's Discretion
- Validation gate output format and CLI shape (must name region and cell on failure), atomic `releases/<ver>` + `current` swap mechanics, repo layout, in-mod attribution display, and the cell-size decision procedure (compile one cell at 256, keep size a config parameter).
- Note for planner: because KnoxMap is the Phase 1 generator, feature-ID anchoring (D-12) must be proven against whatever IDs KnoxMap output exposes; if it exposes none, anchor via geometry hash + tile offset for the spike and revisit when the own generator lands.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUILD-01 | Pinned game/tools/generator/OSM in one PINS file; repeat build without live pull | Verified pin values and hashes (Standard Stack); KnoxMap offline switches `KNOXMAP_PBF_FILE` + `KNOXMAP_OSM_SOURCE=extract`; proxy-poison offline test |
| BUILD-02 | Separate generated/config/edits trees; regen test; orphan report | Tree layout, anchor schema, promote/compose/orphan design; fixture-based pytest regen test |
| BUILD-03 | Connectivity, seam, palette/unmatched-tile, budget gates naming region and cell | Palette from pinned `config/Rules.txt` (licence-clean); BMP seam comparator; vanilla budget baselines measured |
| BUILD-04 | Failed generate/compile leaves last playable export | Staging + atomic `current` swap on Windows (junction vs pointer file), failure-injection test |
| BUILD-05 | OSM attribution, provenance, transformations, asset/licence ledger shown in mod | Verified licence matrix; KnoxMap writes `ATTRIBUTION.txt`; ledger schema |
| PILOT-05 | Cell format, cell count, export size, load time, perf vs budgets | 256 is the engine cell (verified); vanilla size baselines; measurement protocol |
| PILOT-06 | Ramps, basement entrance, ferry-style teleport proven or ruled out | Verified `teleportTo` call; manual protocol with evidence log |
</phase_requirements>

## Summary

The 256-vs-300 question is mostly settled by reading the installed game: the engine cell is 256 tiles (vanilla `map.info` says "Chunk size is 8x8, Cell size is 256x256"), and `spawnpoints.lua` uses absolute `posX/posY/posZ`. What remains open is the **authoring** format: KnoxMap authors in 300-tile source cells (`CELL_SIZE = 300` in `knoxbuild/world.py`) and WorldEd resamples to 256 game cells; the PZ Mapping Tools also offer Native256 projects. So the spike decision is "authoring format of source cells (Legacy300 via KnoxMap vs Native256 hand project)", measured by compiling one cell each way. The game-side grid is always 256.

KnoxMap's pipeline is not a single command. It is: (1) Knoxify-style render of an OSM bbox into three BMPs plus meta via Flask `POST /api/generate` (no standalone CLI for this step found), (2) `python -m knoxbuild output/<map>` to place `.tbx` buildings and write the `.pzw`, (3) `tools/compile_map.py` (patched `PZWorldEd_cli.exe --generate-map=<pzw> [--cells=x0,y0,x1,y1]`), (4) `tools/make_map_mod.py` to package a B42 mod (it omits `lots=` for standalone maps). Offline OSM is supported with two env vars. Buildings are named by index (`<map>_NNNN.tbx`), not OSM ID, so anchors in Phase 1 must be geometry hash + tile offset, as CONTEXT anticipated.

Two facts the planner must act on: (a) the installed game on this machine is on the Steam **`unstable` beta branch**, last updated about 2026-04-21, i.e. it predates 42.20 Stable; PINS cannot record 42.21 until the user opts out of the beta and updates; (b) D-11 names PZ Mapping Tools 43.00B261030, but KnoxMap's patched CLI links against **43.00B260909**; the original research finding was "pin 260909 for Phase 1, 261030 as the Phase 2 target". **SUPERSEDED by the user's post-research decision: Phase 1 pins PZ Mapping Tools 43.00B261030 as the active version; 260909 is kept only as a recorded inactive fallback and is switched to only on explicit user approval after the compatibility check in plan 01-06.** The mismatch risk itself (CLI built on 260909) is unchanged and is what plan 01-06 tests.

**Primary recommendation:** Build a small stdlib-first Python tool (`pa` CLI: pins verify, build, validate, promote, compose, regen-test, release) with pytest fixtures for all automatable criteria; drive KnoxMap as an external pinned black box offline; run the three engine proofs and the vanilla baselines as a scripted manual protocol with a structured evidence log.

## Architectural Responsibility Map

(Game mod build pipeline; tiers are pipeline stages, not web tiers.)

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pinning and verification | Repo tooling (`pa pins`) | — | Pure file/hash check; no game needed |
| Map generation (spike) | External tool (KnoxMap, pinned) | Repo wrapper | Treated as black box; wrapper only sets env, args and captures outputs |
| Edit preservation and orphan report | Repo tooling (composer) | Human (`promote`) | Composer is the only merge point (ARCHITECTURE) |
| Validation gates | Repo tooling | Pinned `Rules.txt` data | Operates on pre-compile BMP/TMX/yaml; compiled lots are opaque |
| Atomic release | Repo tooling | Filesystem | `releases/<ver>` + `current` pointer |
| Compile | External (patched `PZWorldEd_cli.exe`) | — | Unmodified GPL tool run as subprocess |
| Engine proofs and budgets | Human in-game | Repo evidence log + scripts for size stats | AI cannot run Zomboid |
| Attribution display | Mod payload (`ATTRIBUTION.txt`, `map.info`/`description`) | Ledger file in repo | KnoxMap already writes `ATTRIBUTION.txt` |

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Project Zomboid | 42.21 Stable (must switch off `unstable` beta first) | Target runtime | Locked D-11. Installed branch is `unstable` [VERIFIED: D:/SteamLibrary/steamapps/appmanifest_108600.acf — `"BetaKey"		"unstable"`, `"buildid"		"22869276"`] |
| PZ Mapping Tools | **43.00B261030 active for Phase 1 (user decision after research, supersedes the original "260909 for Phase 1" recommendation)**; 43.00B260909 recorded as inactive fallback | WorldEd/TileZed/BuildingEd, `config/Rules.txt` | KnoxMap's CLI is built on 260909 [CITED: KnoxMap worlded/README.md]; compatibility with 261030 is tested in plan 01-06 |
| KnoxMap | **1.8.5.5** (2026-11-08) | Spike generator | Newest release; auto_update must be off [CITED: api.github.com releases] |
| Patched `PZWorldEd_cli.exe` | release `worlded-cli-20260909f` | Headless compile | Pinned by KnoxMap `knoxmap_setup.py` |
| Geofabrik extract | `australia-261108.osm.pbf` (973,794,719 bytes) | Pinned OSM snapshot | Dated copy retained publicly [CITED: download.geofabrik.de] |
| Python | 3.13.14 (Store build, invoked as `python3`) | Pipeline tooling | Locked D-11 [VERIFIED: `python3 --version` → `Python 3.13.14`] |
| pytest | 9.2.0 | Test runner | De facto standard [VERIFIED: pip index versions] |
| PyYAML | 6.0.3 | `edits/features/*.yaml`, `locks.yaml`, `routes.yaml` | Matches ARCHITECTURE config format [VERIFIED: pip index versions] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | 12.3.0 (already installed under Python313 user site) | Read BMPs for palette and seam gates | Palette/seam gates [VERIFIED: site-packages listing `pillow-12.3.0.dist-info`] |
| stdlib `hashlib`, `tomllib`, `json`, `argparse`, `zipfile`, `pathlib`, `os.replace` | — | PINS verify, CLI, release swap | Everything else; no extra deps |
| osmium (pyosmium) | 4.3.2 | NOT needed by Phase 1 tooling | KnoxMap installs its own into its own venv; the repo adds it in Phase 2 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML | JSON/TOML only | Removes a dependency, but ARCHITECTURE and D-12 name `*.yaml`; keep YAML |
| networkx | stdlib union-find | Design-graph connectivity is a ~20 line union-find; defer networkx to Phase 3 |
| `current` as directory junction | `current.txt` pointer file | Junction needs no admin on Windows (`mklink /J`); pointer file is the zero-risk fallback. Recommend pointer file plus an install step that copies/junctions to the game mods dir |

**Installation:**
```bash
python3 -m venv .venv
.venv\Scripts\python -m pip install pytest==9.2.0 pyyaml==6.0.3 pillow==12.3.0
.venv\Scripts\python -m pip freeze > requirements.lock
```
**Version verification:** `pip index versions` run this session: osmium 4.3.2, pytest 9.2.0, pyyaml 6.0.3 current. Note `python` on PATH resolves to a Hermes venv (3.11.15); always call `python3` or the project `.venv` explicitly [VERIFIED: `where python`].

### Pin values gathered this session (go into PINS)
| Item | Value | Source |
|------|-------|--------|
| Tools 260909 zip | `PZ_Mapping_Tools_build20260909f.zip`, 39,759,521 bytes, SHA-256 `2ee15e812bffda6e241c26a2eb2a8f6cd03b0b27bf5899f40196a703f29b5b17` | [VERIFIED: downloaded and `sha256sum` matched GitHub API digest] |
| Tools 261030 zip (ACTIVE in Phase 1 per user decision; also the Phase 2 target) | `PZ_Mapping_Tools_build20261030.zip`, 39,714,067 bytes, SHA-256 `d8913719f9e8dbc194cc829835512f5e364e2fb098e5cc90c3dd3e9eef7f0e1c` | [CITED: GitHub releases API] |
| KnoxMap tag | `1.8.5.5` (annotated tag object sha `14bdc1dd9da0550e419a5434a3ea26b64d15aba3`; also pin the dereferenced commit) | [CITED: GitHub git/ref API] |
| KnoxMap windows zip | `KnoxMap-v1.8.5.5-windows.zip`, 4,039,241 bytes, SHA-256 `1b65a3213cac92c8a30990a426d01abb634d099db7a05ccd6b7413e6adc27cea` | [CITED: GitHub releases API] |
| Patched CLI | URL `https://github.com/spytheeuclidean-a11y/knoxmap/releases/download/worlded-cli-20260909f/PZWorldEd_cli.exe`, SHA-256 `dbae186f1f1f541decd123604ec9fc822d930f8f7c1ec8b17c1b89874628f3e2` | [CITED: knoxmap_setup.py at tag 1.8.5.5: `CLI_SHA256 = "dbae186f1f1f541decd123604ec9fc822d930f8f7c1ec8b17c1b89874628f3e2"`] |
| OSM extract | `australia-261108.osm.pbf`, MD5 `02b472d2aee85e865a6afd44fa00d30c` (Geofabrik publishes MD5 only); compute and record SHA-256 yourself on first download | [CITED: australia-261108.osm.pbf.md5] |
| LICENSES.md hash | Compute at tag 1.8.5.5 when vendoring (not yet computed) | — |

Caveats the PINS file must handle:
- KnoxMap `Setup.bat` downloads the tools zip with **no checksum check** (`TOOLS_URL` has no hash) [CITED: knoxmap_setup.py]. So `pa pins verify` must hash the vendored tools itself (zip hash before Setup, or a tree manifest of `vendor/PZMappingTools` after).
- Geofabrik MD5 comes from the same server as the file: it proves transfer integrity, not authenticity. Treat SHA-256 as trust-on-first-use and record the download date.
- KnoxMap's extract cache expires after 14 days and sends `If-Modified-Since` to refresh [CITED: generator/extract.py]. Using `KNOXMAP_PBF_FILE` (user-supplied file) bypasses this entirely.

## Package Legitimacy Audit

`gsd-tools query package-legitimacy check --ecosystem pypi` returned `SUS` for all checked packages with reasons `too-new` and/or `unknown-downloads` (download counts were unavailable from the seam, not low). These are long-established projects with known source repos; the SUS is a tooling limitation. Per protocol the planner adds one `checkpoint:human-verify` before the first `pip install`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pytest | PyPI | long-established | unavailable | github.com/pytest-dev/pytest | SUS (too-new release 2026-10-27, unknown-downloads) | Flagged — single human-verify checkpoint before install |
| pyyaml | PyPI | long-established | unavailable | pyyaml.org | SUS (unknown-downloads) | Flagged — same checkpoint |
| pillow | PyPI | long-established, already installed locally | unavailable | github.com/python-pillow/Pillow | SUS (too-new release, unknown-downloads) | Flagged — same checkpoint |
| osmium | PyPI | long-established | unavailable | osmcode.org/pyosmium | SUS (too-new, unknown-downloads) | Not installed in Phase 1 (YAGNI) |

**Packages removed due to SLOP verdict:** none
**Packages flagged SUS:** pytest, pyyaml, pillow (planner inserts one checkpoint; pin via `requirements.lock` with hashes if desired)
Package names here came from project STACK research and the pytest/PyYAML/Pillow names are standard; they are tagged [ASSUMED] for name provenance until the human checkpoint confirms.

## Architecture Patterns

### System Architecture Diagram

```
 PINS.toml ──> pa pins verify ──(fail: stop)──────────────────────────────┐
     │ pass                                                               │
     v                                                                    │
 sources/ (pbf, tool zips; hashed) ──> vendor/ (tools, KnoxMap, CLI)      │
     │                                                                    │
     v        env: KNOXMAP_PBF_FILE, KNOXMAP_OSM_SOURCE=extract,          │
 pa build ──> proxy-poison (HTTP(S)_PROXY=127.0.0.1:9), auto_update=false │
     │                                                                    │
     ├─ 1 KnoxMap Flask (127.0.0.1) POST /api/generate {bbox,mapName,...} │
     │      -> output/<map>/{<map>.bmp,_veg.bmp,_ZombieSpawnMap.bmp,meta} │
     ├─ 2 python -m knoxbuild output/<map>  -> buildings/*.tbx, <map>.pzw │
     ├─ 3 PZWorldEd_cli.exe --generate-map=<map>.pzw [--cells=...]        │
     │       -> tmx/ + lots/ (lotheader, lotpack, chunkdata)              │
     v                                                                    │
 generated/ (disposable, hash-stamped)                                    │
     │                         edits/ (features/*.yaml, overlays/*.tmx,   │
     │                                 locks.yaml)  <── pa promote (human)│
     v                                       │                            │
 pa compose: resolve anchors ── orphans.json + table ──(--strict: exit≠0) │
     │ composed/                                                          │
     v                                                                    │
 pa validate (design graph, seam, palette, budget) ──fail: names region+cell
     │ pass                                                               │
     v                                                                    │
 pa release: staging/<ver> -> releases/<ver> -> repoint current ◄─────────┘
     │ (any earlier failure leaves `current` untouched)
     v
 install copy to %USERPROFILE%\Zomboid\mods\<id>  -> human in-game protocol
```

### Recommended Project Structure
```
PINS.toml                 # all pins, hashes, download dates
requirements.lock
config/                   # world.yaml (cell_size param), budgets.yaml, routes.yaml (fixture), palette note
sources/                  # git-ignored; pbf + zips (large). Put on D: (see Environment)
vendor/                   # git-ignored; KnoxMap, PZMappingTools (verified by pins)
generated/                # disposable
edits/                    # features/*.yaml, overlays/<region>/<cx>_<cy>.tmx, locks.yaml
composed/  releases/<ver>/  current.txt
reports/                  # gate JSON + orphans.json
ledger/                   # licences.yaml, assets.yaml, provenance.json
pa/                       # python package: pins.py, build.py, compose.py, gates/*.py, release.py, cli.py
tests/                    # pytest, fixtures under tests/fixtures
spike/                    # evidence: protocol.md, evidence/<feature>/..., decision.md, vanilla-baseline.json
```
One package `pa` with a handful of modules; do not add abstractions beyond this.

### Pattern 1: Offline KnoxMap invocation (BUILD-01)
**What:** Wrapper sets env and a poisoned proxy, runs steps 1 to 3, hashes outputs.
**Verified switches:** `KNOXMAP_PBF_FILE` env, then `pbf_file` config key, selects a user-supplied file; `forced()` is true when set [CITED: generator/extract.py]. `KNOXMAP_OSM_SOURCE=extract` makes failure raise instead of falling back to Overpass [CITED: generator/osm.py]. `"auto_update": false` in `knoxmap_config.json` [CITED: README].
```python
env = {**os.environ,
  "KNOXMAP_PBF_FILE": str(pbf), "KNOXMAP_OSM_SOURCE": "extract",
  "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
  "NO_PROXY": "127.0.0.1,localhost", "KNOXMAP_NO_DISCORD": "1"}
```
The proxy poison is the BUILD-01 "no live pull" proof: build must succeed with it (and the log must contain no "Overpass"). Caveat: the Flask `before_request` rejects non-localhost Host headers, fine for 127.0.0.1 [CITED: app.py]. Pass an explicit `mapName` to `/api/generate` (a missing name falls back to a timestamp, which breaks repeatability) [CITED: web/generation.py].

### Pattern 2: Hybrid edit anchoring (BUILD-02)
**Anchor schema (recommended, YAML):**
```yaml
- edit_id: pilot-bldg-0042-sign
  kind: feature            # feature | overlay | lock
  anchor:
    type: footprint        # footprint | osm_way | osm_node | cell_tile
    ref: "<map>_0042"      # KnoxMap tbx index (unstable across rebuilds)
    geom_hash: "sha256:..."# hash of normalised footprint polygon (tile coords relative to its own min corner)
    tile: [cx, cy, lx, ly] # last-known 256-cell and local tile
    tolerance_tiles: 2
  payload: overlays/<region>/<cx>_<cy>.tmx#layer=hand_01
  generated_tiles_hash: "sha256:..."   # recorded by promote (D-13)
```
Resolution order: exact `geom_hash` match anywhere (survived, record move distance) → `ref` match with hash mismatch (`hash_mismatch`) → nothing found (`missing_source`) → found beyond tolerance (`moved_beyond_tolerance`). KnoxMap numbers buildings by index [CITED: KNOXBUILD.md], so index alone must never be the anchor; the geometry hash is. Whether the Knoxify `buildings GeoJSON` carries OSM ids is **unknown** and must be inspected in the first spike task; if it does, prefer `osm_way` anchors.

### Pattern 3: Atomic release on Windows (BUILD-04)
Build into `staging/<ver>`, run gates, `os.replace(staging, releases/<ver>)` (same volume), then write `current.txt` via temp file + `os.replace` (atomic on NTFS). Installer reads only `current.txt`. Failure test: inject a compile failure (bad `.pzw` path or monkeypatched exit code) and assert `current.txt` and `releases/<prev>` byte-identical before and after.

### Pattern 4: Gate output (Claude's discretion)
Every gate returns a list of `Finding(gate, region, cx, cy, tile, message)`; CLI prints `GATE FAIL <gate> region=<r> cell=<cx>_<cy> tile=<x>,<y>: <msg>`, writes `reports/<gate>.json`, exits non-zero. A fixture "broken world" test asserts the region and cell appear in stdout.

### Anti-Patterns to Avoid
- **Copying `generator/pz_colors.py` or any Knoxify-derived file for the palette:** unlicensed, forbidden by D-10. Read colours from the pinned tools' `config/Rules.txt` at runtime instead.
- **Letting KnoxMap Setup run unattended:** it fetches the tools with no hash check. Verify, then use.
- **Using the KnoxMap UI for repeat builds:** window plus Nominatim need network; drive `app.py` on localhost or call the same functions.
- **Deleting orphaned edits or auto-placing them** (D-14).
- **Treating a clean compile as done:** completion is the human in-game protocol.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Palette definition | A colour table | Parse pinned `config/Rules.txt` (`rule { label, bitmap, color = R G B, tiles, layer }`, 91 rules counted on the 260909 zip; recount on the pinned 261030 tree, plan 01-08 records the number) | Authoritative, GPL tool data, licence-clean [VERIFIED: extracted from 260909 zip `config/Rules.txt`] |
| Hashing / manifests | Custom digest code | `hashlib.sha256`, tree manifest as sorted `path sha256` lines | Standard, deterministic |
| Map compile | Own lotpack writer | Patched `PZWorldEd_cli.exe --generate-map` | Binary format undocumented |
| Cell size/stat reporting | Parsing lotpack | File sizes of `world_X_Y.lotpack`, `X_Y.lotheader`, `chunkdata_X_Y.bin` | Sizes are all the budget needs |
| OSM reading | Parser | KnoxMap's own pyosmium (Phase 1); pyosmium in Phase 2 | Not needed by Phase 1 tooling |
| Test framework | Ad hoc scripts | pytest with `tmp_path` fixtures | Regen test needs temp trees |

**Key insight:** Phase 1 tooling is glue plus gates plus a manual evidence protocol. The expensive unknowns are in the game, not in code.

## Runtime State Inventory

Not a rename/refactor/migration phase. Greenfield; omitted per template. One real runtime-state item: **saves are cell-by-cell and a rebuilt map leaves old cells beside new ones, so every rebuild needs a new save** [CITED: STACK.md]; the protocol must create a fresh save per build.

## Common Pitfalls

### Pitfall 1: Pinning a game build that is not 42.21 Stable
**What goes wrong:** PINS says 42.21 but the install is on the `unstable` beta from April 2026.
**Why:** Steam `BetaKey "unstable"`, `LastUpdated` 1776746348 (about 2026-04-21, computed) [VERIFIED: appmanifest_108600.acf]. 42.20 Stable shipped 2026-07-29 [CITED: STACK.md, MEDIUM].
**Avoid:** First task: user switches Steam Betas to "None" and updates; then PINS records Steam `buildid`, the in-game version string (screenshot of the main menu) and manifest id. Re-measure vanilla baselines after the switch (the numbers below came from the old install).
**Warning sign:** `pa pins verify` compares appmanifest `buildid`/`BetaKey` against PINS and fails on drift.

### Pitfall 2: Tools-version mismatch with KnoxMap's CLI
Mixing 261030 tools with the CLI linked to 260909 Qt libs [CITED: STACK.md, worlded/README.md]. Original advice: pin 260909 for Phase 1. **Superseded by the user decision: pin 261030 (active) and test the mismatch early in plan 01-06; 260909 is the recorded inactive fallback, never switched silently (user approval recorded in PINS.toml `[tools.active.approval]`).**

### Pitfall 3: Silent network use
`osm_source` "auto" and "overpass" can reach the network; Nominatim place search and the updater also do [CITED: osm.py, README]. Use the explicit env, `auto_update=false`, and the poisoned-proxy test; do not rely on "extract found, so it is fine".

### Pitfall 4: Non-repeatable outputs
Timestamp fallback map name; presets chosen "seeded per footprint" (deterministic) [CITED: KNOXBUILD.md] but lot binaries may embed timestamps. Define success criterion 1 as: identical PINS + identical input hashes + **identical BMP and `.pzw`/`.tbx` hashes** across two runs; record whether `.lotpack` bytes also match (do not assume). [ASSUMED]

### Pitfall 5: TMX/BMP handling assumptions
TMX layer encoding (CSV vs base64/zlib) not verified; limited to 300x300 tiles per map [CITED: PZ_Mapping_Tools README]. First task must open one KnoxMap `tmx/` file.

### Pitfall 6: Disk
Repo volume F: has about 4.9 GB free [VERIFIED: `df -h /f`]; the Australia PBF alone is 974 MB and KnoxMap caches more. Put `sources/`, `vendor/`, `generated/` outputs on D: (844 GB free) via config paths, keep F: for text.

### Pitfall 7: Measuring with a contaminated baseline
Different save, different mods, or debug overhead skew load time/FPS. Fixed protocol below; same machine, same settings, no other mods for baseline runs, 3 runs, median.

### Pitfall 8: Orphan test that only tests the happy path
D-15's perturbation step must assert *exactly* the intended edits orphan and all other composed output is byte-identical.

## Code Examples

### Vanilla cell-size baseline (script task, automated)
Measured this session on the installed (old, `unstable`) Muldraugh folder; re-run after switching to Stable:
- 4065 cells; `world_N_N.lotpack` total 3991.5 MB, avg 0.98 MB, min 55,000 B (`world_77_62.lotpack`), max 2,982,112 B (`world_49_6.lotpack`); lotheaders 28.25 MB; chunkdata 10.88 MB [VERIFIED: `ls -la` of `media/maps/Muldraugh, KY`]
- Quoted verbatim: `description=Chunk size is 8x8, Cell size is 256x256` [VERIFIED: media/maps/Muldraugh, KY/map.info]
- Files per cell: `N_N.lotheader`, `world_N_N.lotpack`, `chunkdata_N_N.bin` (4065 each) [VERIFIED: directory listing]
- Muldraugh `map.info` has no `lots=` line; Rosewood has `lots=Muldraugh, KY` [VERIFIED: map.info files] — so the file format permits a standalone map, but an in-game load test is still required.

```python
# pa/stats.py: MB per cell from a map folder, split populated/empty by lotpack size threshold
import re, pathlib
def cell_stats(map_dir):
    out = {}
    for p in pathlib.Path(map_dir).glob("world_*_*.lotpack"):
        cx, cy = map(int, re.fullmatch(r"world_(\d+)_(\d+)\.lotpack", p.name).groups())
        out[(cx, cy)] = p.stat().st_size
    return out  # threshold for "empty" is a recorded config value, not a guess
```

### Spawnpoints format (cell-size/format evidence)
```lua
-- Source: media/maps/Muldraugh, KY/spawnpoints.lua (installed game)
function SpawnPoints()
return {
  chef = {
    { posX = 10606, posY = 9474, posZ = 0 },
```
[VERIFIED: spawnpoints.lua lines 1-5]. KnoxMap's packager writes a single `unemployed` list with the same `posX/posY/posZ` and shifts points by the world origin [CITED: tools/make_map_mod.py].

### Teleport call for the ferry-style proof
```lua
-- Source: media/lua/client/DebugUIs/ISFastTeleportMove.lua line 12 (installed game)
player:teleportTo(x, y, player:getZ())
-- Source: media/lua/client/DebugUIs/DebugContextMenu.lua line 1178
getPlayer():teleportTo(tonumber(x), tonumber(y), tonumber(z))
```
[VERIFIED: grep output of both files this session; the line numbers are from `grep -n`, content read in grep output not a full `Read`]. The older "setX/setLx" recipe in STACK.md is not required for a first attempt; use `teleportTo`. Vehicle transfer has no verified API: treat as attempt 2 / separate implementation (D-02 needs two different implementations before RULED OUT).

### Mod layout KnoxMap emits (B42)
```
<mods>/<mod_id>/mod.info (also common/ and 42/), poster.png, ATTRIBUTION.txt,
common/media/maps/<Map Name>/{*.lotheader,*.lotpack,chunkdata_*.bin,map.info,spawnpoints.lua,objects.lua,spawnSelectImagePyramid.zip}
```
[CITED: tools/make_map_mod.py]. The installed game's own `mods/examplemod` is a B41-style layout (`mod.info` + `media/` at root, no `42/`) [VERIFIED: `find mods/examplemod`], so it is not a B42 reference; rely on KnoxMap's emitted layout and confirm the mod is visible in the in-game mod list.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy300 projects, `worldX/worldY` spawns | Native256 projects, absolute `posX/posY/posZ` | PZ Mapping Tools for 42.20+ | KnoxMap's 300-cell authoring is the legacy path [CITED: PZ_Mapping_Tools README] |
| Single worldmap grid | 256-square worldmap XML/bin normalised by "Write Worldmap" | 42.20 | World map is generated by the tools, not hand written [CITED: README] |
| 42.21 latest | 42.22 on Pre-Release, no sign of Stable as of search | 2026-10-27 | Recheck before final pin [CITED: supercraft.host via WebSearch, MEDIUM] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `.lotpack` bytes may not be reproducible across identical-input builds; criterion 1 defined on BMP/pzw/tbx hashes | Pitfall 4 | If lots are reproducible, can tighten; if neither is, success criterion 1 needs user to accept the weaker definition |
| A2 | New-save load time can be taken from `console.txt` timestamps or a stopwatch/screen capture; no in-game timer API verified | Validation Architecture | Measurement method may need changing; effect is on D-06 repeatability |
| A3 | Driving FPS can be recorded with an external overlay (e.g. NVIDIA/PresentMon); no verified in-game FPS log | Validation Architecture | Same |
| A4 | Save-size growth is measured from the `Zomboid/Saves` folder size | Validation Architecture | Folder layout in B42 unverified (no `~/Zomboid` exists yet on this machine) |
| A5 | Python packages pytest/pyyaml/pillow are the right names (standard, but not authority-verified this session) | Package Legitimacy | Low; human checkpoint |
| A6 | TMX layer data encoding in KnoxMap output is parseable without Qt | Pitfall 5 | Overlay drift check may need to hash raw layer text instead of tile ids |
| A7 | KnoxMap `buildings GeoJSON` may contain OSM ids | Pattern 2 | If absent, geometry-hash anchors only (already the fallback) |
| A8 | A headless run of KnoxMap via `python app.py` + POST `/api/generate` works without the pywebview window | Pattern 1 | If it needs the window, call `renderer.render` directly or script with a browser |
| A9 | KnoxMap `standalone` placement is set per project (`placement.standalone(project_dir)`); how the user sets it is not shown | Open Questions | Spike may need the UI "Game world" toggle once; record the resulting project file |
| A10 | Real USA is installed? RESOLVED by user: not installed; baseline is vanilla only | Vanilla baselines | none |

## Open Questions

**Resolution status (revision pass 1):** every question below is resolved or assigned to a named plan task.

| Q | Status | Resolution / owner |
|---|--------|--------------------|
| Q1 | RESOLVED | User decided: pin 261030 active, 260909 inactive fallback (see Summary, Standard Stack, Pitfall 2 annotations) |
| Q2 | ASSIGNED | 01-12 Task 2 (recheck 42.22 in Steam, record in PINS [game]) |
| Q3 | ASSIGNED | 01-06 Task 2 (standalone + one-cell bbox, padding recorded in spike/compat-261030.md) |
| Q4 | ASSIGNED | 01-08 Task 1 (spike/inspection.md `anchor_type`, OSM id exposure) |
| Q5 | ASSIGNED | 01-08 Task 3 (Native256 .pzw via patched CLI, spike/cell-format-compare.md) |
| Q6 | RESOLVED | User: Real USA is not installed; baseline is vanilla Muldraugh only (recorded in 01-01 Task 1 `real_usa_installed: false`) |
| Q7 | RESOLVED | Settled by D-10: Knoxify files not copied; ledger row only (01-05 Task 2) |

Original text kept below.

1. **D-11 vs KnoxMap tools version.** *(RESOLVED by user decision: 261030 active, 260909 fallback; the "recommended 260909" line below is superseded.)*
   - Known: D-11 says 261030; KnoxMap's patched CLI is built on 260909 and links its Qt libs.
   - Unclear: whether the user wants 260909 pinned for Phase 1 (recommended).
   - Recommendation: PINS holds `tools.phase1 = 260909`, `tools.phase2_target = 261030`; confirm with user at plan time.
2. **Is 42.22 Stable yet?** Last search: Stable still 42.21, 42.22 Pre-Release since 2026-10-27 [MEDIUM]. Recheck in Steam at pin time.
3. **KnoxMap standalone mode and a one-cell area.** How to force standalone (no `lots=`) and a minimal cell from the API; whether a bbox smaller than one cell is padded to a whole cell ("the game needs whole cells") [CITED: README].
4. **What IDs does Knoxify output expose?** Inspect `buildings GeoJSON` and `<map>_placements.csv` (fields: tile/cell coordinates, room and furniture counts) in task 1.
5. **Native256 hand-built cell path.** Whether the patched CLI `--generate-map` accepts a Native256 `.pzw` (it is built from the same tools, so likely) and what a minimal Native256 project needs. Needed to compare 256 vs 300 on equal footing.
6. **Real USA installed/baseline?** Ask the user; otherwise vanilla only.
7. **Knoxify licence.** KnoxMap says unpublished; STACK says GitHub API reports MIT. D-10 settles Phase 1 policy: not copied. No action beyond ledger rows.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | tooling | ✓ (`python3`) | 3.13.14 | `python` resolves to a 3.11.15 Hermes venv: always call `python3`/`.venv` |
| pip / venv | tooling | ✓ | pip 26.1.2 | — |
| pytest | tests | ✗ | — | `pip install` (after human-verify checkpoint) |
| Git | repo | ✓ | 2.56.0 | — |
| Node | gsd tooling only | ✓ | v26.12.1 | — |
| Project Zomboid | engine proofs | ✓ but wrong branch | `unstable` beta, buildid 22869276, updated ~2026-04-21 | User must opt out of beta and update to 42.21 Stable |
| `%USERPROFILE%\Zomboid` | mods dir, saves, console.txt | ✗ (does not exist yet) | — | Created on first game launch; game must be run once |
| osmium-tool CLI | not needed in Phase 1 | ✗ | — | none needed |
| PZ Mapping Tools / KnoxMap | build | ✗ (not yet downloaded) | — | Download and verify per PINS (tools zip fetched to scratch this session; hash matched) |
| Disk | sources/builds | F: 4.9 GB free, D: 844 GB free | — | Put big dirs on D: |
| Reference machine | PILOT-05 | ✓ | Intel Core i9-10885H, NVIDIA GeForce RTX 2080 Super with Max-Q, 32 GB RAM; SSD model not recorded | Record SSD model in spike log [VERIFIED: CIM query] |
| Microsoft VC++ x64 Redistributable | KnoxMap | unknown | KnoxMap requires 14.51.36247+ [CITED: README]; PZ Mapping Tools bundle their own runtime | Install if KnoxMap Setup complains |
| Internet | one-time downloads only | ✓ | — | Builds themselves run with proxy poison |

**Missing with no fallback:** PZ on Stable branch (user action). **Missing with fallback:** all others above.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.2.0 on Python 3.13 (.venv), Windows |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — none yet, Wave 0 |
| Quick run command | `.venv\Scripts\python -m pytest tests -x -q` |
| Full suite command | `.venv\Scripts\python -m pytest tests -q` plus `pa pins verify` and (optional, slow) `pa build --check-repeat` |

Per user global rule: local unit tests only; no deployed test environment applies to a game mod. In-game checks are manual and recorded.

### Success Criteria → Verification Map

| # | Criterion | Check | Type | Command / Evidence | File Exists? |
|---|-----------|-------|------|--------------------|--------------|
| 1 | Build repeats from PINS with no live pull | PINS schema + every hash verified; build twice with proxy poison, compare BMP/pzw/tbx hash manifest; log has no Overpass/network | automated (slow, needs vendored tools) + unit tests for verify with fixture files | `pytest tests/test_pins.py`; `pa build --check-repeat` | ❌ Wave 0 |
| 2 | Hand edit survives; orphan reported | Fixture generated tree + `edits/`; delete `generated/`, regen, compose, assert edit hashes unchanged and present; perturb inputs and assert exact orphan set and reason codes; `--strict` exits non-zero | automated | `pytest tests/test_regen.py tests/test_orphans.py` | ❌ Wave 0 |
| 3 | Broken connectivity/seam/palette tile fails naming region and cell | Fixture worlds each broken one way: design graph with isolated node, two BMP cells with road offset at seam, BMP with colour not in `Rules.txt`; assert non-zero exit and `region`/`cell` in output and JSON | automated | `pytest tests/test_gates.py` | ❌ Wave 0 |
| 4 | Failed generation/compile leaves last playable export | Release store with prior `releases/<v1>`, `current.txt`=v1; inject failure at generate and at compile; assert `current` and v1 tree unchanged, partial staging cleaned or quarantined | automated | `pytest tests/test_release.py` | ❌ Wave 0 |
| 5 | Decision record: cell format, MB per populated/empty cell, new-save load time, ramps/basement/ferry verdicts | Scripted size stats (automated) + human protocol runs with evidence log; decision file completeness check | semi-manual: `pa stats <map_dir>`; manual in-game; automated check that the decision file has every required field | `pytest tests/test_decision_record.py` (schema check) + human evidence | ❌ Wave 0 |

### Automated vs Manual
- **Automated (pytest on Windows):** PINS verify, offline-build wrapper behaviour (with a fake KnoxMap stub for unit tests), compose/orphan logic, all four gates on fixtures, release atomicity, stats, ledger/attribution presence check, decision-record schema check.
- **Automated but needs real tools (integration, run by hand or CI-less):** real KnoxMap build with proxy poison and repeat-hash comparison; real `PZWorldEd_cli.exe` one-cell compile.
- **Manual in-game (human plays, per D-01):** new-save loads the cell standalone; spawn works; ramp/basement/ferry trials with save/reload; vanilla vs pilot load time, FPS, stream-in; ATTRIBUTION visible in mod. AI cannot run Zomboid. Evidence log format below.

### Manual protocol and evidence log layout (recommended)
```
spike/protocol.md                      # step lists copied from D-03, with checkboxes
spike/evidence/<feature>/<attempt>/    # run.yaml, console.txt excerpt, screenshots/*.png
spike/vanilla-baseline.json            # machine, build, run1..3, median
spike/decision.md                      # cell format, MB/cell (populated/empty), load time, verdicts
```
`run.yaml` fields (D-04): `build`, `mod_version`, `date`, `trials: [{n, direction, pass, note}]`, `reload_result`, `console_errors`, `screenshots`, `verdict` (PROVEN | RULED OUT | INCONCLUSIVE), `next_step`. A pytest schema check enforces: PROVEN requires every trial `pass: true` and `reload_result: pass`; RULED OUT requires two attempts with different `implementation` values and a non-empty `logged_cause`.

Measurement notes: always start a brand-new save per build (old cells persist [CITED: STACK.md]); use `-debug` launch for the teleport UI (`DebugContextMenu.onTeleportUI` exists in the installed Lua) [VERIFIED: DebugContextMenu.lua lines 1134-1178 via grep]; record load time as median of 3 from first click on "Start" to controllable character [ASSUMED method, A2]; MB per cell from file sizes; save growth from the save folder after N minutes walking [ASSUMED, A4].

### Sampling Rate
- **Per task commit:** `.venv\Scripts\python -m pytest tests -x -q`
- **Per wave merge:** full pytest plus `pa pins verify`
- **Phase gate:** full suite green, real KnoxMap repeat-build check done, spike evidence complete before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `pyproject.toml` with pytest config; `.venv` + `requirements.lock`
- [ ] `tests/fixtures/` tiny BMP cells, `Rules.txt` excerpt, routes fixture, edits fixture
- [ ] `tests/test_pins.py`, `test_regen.py`, `test_orphans.py`, `test_gates.py`, `test_release.py`, `test_decision_record.py`
- [ ] Fake-KnoxMap stub for wrapper unit tests

## Security Domain

Applies focused security-audit guidance to the touched surface (supply chain, downloads, local server, secrets). No auth, sessions or user input beyond local CLI.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Validate YAML/JSON with explicit schema checks; `yaml.safe_load` only; reject path traversal in edit payload paths; `zipfile` extraction with member path checks |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256`; no custom crypto |
| V10 Malicious Code / V14 Config | yes | Hash-pinned downloads, no live execution of unverified binaries, `auto_update` off, lockfile |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Tampered or swapped tool binary (`PZWorldEd_cli.exe`, tools zip, KnoxMap zip) | Tampering | Verify SHA-256 against PINS before first run and before every build; fail closed |
| KnoxMap Setup downloads tools without a hash [CITED: knoxmap_setup.py] | Tampering | Pre-verify the zip or tree manifest; do not trust Setup's own check for the tools |
| Same-server MD5 for the OSM extract | Tampering | Record own SHA-256 at first download; treat as TOFU; re-verify each build |
| Running downloaded code from its own directory | Elevation | Extract each download into a fresh empty dir; run Python with `-I`; pass paths as args; never run from inside the extracted tree |
| Zip slip when extracting | Tampering | Validate member names before `extractall` |
| KnoxMap local Flask server on 127.0.0.1:5000 | Info disclosure | Binds loopback and rejects foreign Host/Origin [CITED: app.py]; run only during build, kill after |
| Telemetry / network in builds (Discord presence, updater, Nominatim) | Info disclosure | `KNOXMAP_NO_DISCORD=1`, `auto_update=false`, proxy poison |
| `yaml.load` arbitrary object construction | Tampering | `yaml.safe_load` only |
| Unpinned Python deps | Tampering | `requirements.lock` (pip freeze) |

## Licence ledger rows (BUILD-05)
| Component | Licence | Handling | Source |
|-----------|---------|----------|--------|
| OSM data (Geofabrik extract) | ODbL 1.0; credit "© OpenStreetMap contributors" | Attribution in mod (`ATTRIBUTION.txt` is written by KnoxMap) and `map.info` description; provenance JSON records extract date `australia-261108` and transformations (KnoxMap render, scale, rotation) | [CITED: KnoxMap LICENSES.md] |
| Patched `PZWorldEd_cli.exe`, `worlded/` | GPL-2.0-or-later | Run unmodified as external tool; source offer lives with the release; if redistributed, ship source | [CITED: KnoxMap LICENSES.md] |
| PZ Mapping Tools | GPL-2.0 | External tool, not redistributed | [CITED: STACK.md] |
| Knoxify-derived files | no licence published, all rights reserved | **Not copied**; row records "not copied, licence unpublished" | [CITED: KnoxMap LICENSES.md] |
| KnoxMap own additions (`knoxbuild/`, `tools/`) | MIT | Used as external tool | [CITED: KnoxMap LICENSES.md] |
| Project Zomboid tiles/art | The Indie Stone copyright | Never redistribute; tools read from player's own install | [CITED: KnoxMap LICENSES.md] |
| Generated mod payload | contains ODbL-derived data | ODbL posture/legal check deferred to Phase 5 (REL-02) | [ASSUMED] |

"Shown in the mod" can be satisfied minimally in Phase 1 by shipping KnoxMap's `ATTRIBUTION.txt` plus an attribution line in `map.info` description; confirm the description renders in the in-game map picker during the manual test.

## Sources

### Primary (HIGH confidence)
- Installed game files (this session): `media/maps/Muldraugh, KY/map.info`, `spawnpoints.lua`, directory listings and sizes; `media/lua/client/DebugUIs/ISFastTeleportMove.lua`, `DebugContextMenu.lua`; `steamapps/appmanifest_108600.acf`
- PZ Mapping Tools 43.00B260909 zip downloaded and hashed; `config/Rules.txt` read (https://github.com/Unjammer/PZ_Mapping_Tools/releases)
- GitHub APIs: KnoxMap releases and tag ref; PZ Mapping Tools releases
- KnoxMap source at tag 1.8.5.5: `knoxmap_setup.py`, `generator/extract.py`, `generator/osm.py`, `web/generation.py`, `knoxbuild/world.py`, `tools/make_map_mod.py`, `app.py`, `KNOXBUILD.md`, `LICENSES.md`, `worlded/README.md`, `README.md` (https://github.com/spytheeuclidean-a11y/knoxmap)
- Geofabrik australia page and `.md5` (https://download.geofabrik.de/australia-oceania/)

### Secondary (MEDIUM confidence)
- PZ Mapping Tools README for Native256, spawnpoints and worldmap behaviour
- Project STACK/ARCHITECTURE/PITFALLS/SUMMARY research (prior session)
- WebSearch on 42.22 status (supercraft.host guide, last updated 2026-10-27)

### Tertiary (LOW confidence)
- Measurement methods for load time, FPS and save growth (training knowledge)
- Whether lot binaries are reproducible

## Metadata

**Confidence breakdown:**
- Standard stack and pins: HIGH. Hashes verified or taken from vendor APIs; one zip hashed locally.
- Architecture: MEDIUM. Tool flow known; headless Flask drive and Native256 CLI path unproven.
- Pitfalls: MEDIUM. Branch mismatch and hash-less Setup are verified; reproducibility is assumed.
- Engine proofs: LOW until the user plays; only `teleportTo` is verified present.

**Research date:** 2026-11-09
**Valid until:** 2026-11-16 for KnoxMap (releases almost daily); 30 days for the rest
