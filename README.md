# Project Australia

A planned Project Zomboid (Build 42) map mod that recreates twelve mainland Australian cities and towns as playable survival districts, joined by one continuous, driveable highway network. Tasmania, reached by a Bass Strait ferry, is a separate late decision that depends on a feasibility test.

## Status

Early. Phase 1 of 6 (toolchain spike and pipeline foundations) is in progress. There is no playable map yet and nothing here is installable as a mod. The repository currently holds the build and verification tooling and the planning documents.

## Goal

Road trips are part of survival. Each city is a distinct district, and the drives between them run on physical roads with no fast travel on the mainland. Cities and highway corridors are scaled separately so streets and buildings stay usable while drives stay worth taking. The planned destinations are Melbourne, Geelong, Sydney, Canberra, Gold Coast, Brisbane, Cairns, Darwin, Broome, Perth, Coober Pedy and Adelaide.

Not goals: a full 1:1 Australia, every suburb or town, surveyed-accurate interiors, a drivable ship simulation, multiplayer or Workshop publication (for now), or a period setting. The map is present-day. See [.planning/PROJECT.md](.planning/PROJECT.md).

## What exists today

The `pa` command line tool, written in Python, builds and checks a map from pinned inputs:

- **Pinned inputs.** `PINS.toml` records the game build, tool versions and checksums, and the OpenStreetMap extract. `pa pins verify` checks them.
- **Edit-safe regeneration.** Generated geography and hand edits live in separate trees (`edits/`), so regenerating does not overwrite hand edits.
- **Validation gates.** Palette, road connectivity, cell seam and budget checks (`config/gates.yaml`).
- **Atomic release.** A composed map is promoted only after the gates and the licence check pass.
- **Provenance ledger.** `ledger/` records the hash manifests and licences for third-party tools and data.
- **Measurement and decision protocol.** `spike/protocol.md` and the stats and decision-record validators define how scale, budget and engine questions get answered with evidence.

## Layout

| Path | Contents |
|------|----------|
| `pa/` | Build and verification tooling |
| `tests/` | Unit tests, with a fake KnoxMap fixture for offline runs |
| `config/` | Settings for the world, the gates and KnoxMap |
| `edits/` | Hand-authored edits kept apart from generated output |
| `ledger/` | Hash manifests and the licence ledger |
| `spike/` | Compatibility and measurement notes, spike templates |
| `PINS.toml` | Pinned versions and checksums |
| `.planning/` | Project plan, requirements, roadmap and per-phase plans |

## Running the tests

Windows with Python 3.13:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pytest
```

The default run skips tests marked `integration`, which need the game or the external mapping tools. The full build needs a Project Zomboid install, the pinned PZ Mapping Tools and a data directory (`D:/PA` by default, set in `config/world.yaml`). Those are not included here.

## How it is planned

Work is planned and tracked in [.planning/](.planning/) with the GSD workflow. Start with [PROJECT.md](.planning/PROJECT.md) and [ROADMAP.md](.planning/ROADMAP.md). The roadmap runs from the toolchain spike, through a Melbourne to Geelong pilot that decides scale, to a national road network, selective features, a release gate and the conditional ferry.

## Credits and licensing

The code in this repository is MIT licensed (see [LICENSE](LICENSE)).

- Map data comes from OpenStreetMap, which is available under the Open Database Licence. Credit: (c) OpenStreetMap contributors.
- KnoxMap and PZ Mapping Tools are used as pinned external tools. They are not bundled or redistributed here, and keep their own licences (recorded in `ledger/licences.yaml`).
- Project Zomboid belongs to The Indie Stone. This is an unofficial fan project with no affiliation to them, and no game assets are included.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports go through [SECURITY.md](SECURITY.md).
