# Contributing

Project Australia is early and mostly maintained by one person, so expect replies within about a week, not hours. Keep the discussion on GitHub.

## Before you start

Read [README.md](README.md) and [.planning/PROJECT.md](.planning/PROJECT.md). The project goal and the out-of-scope list there decide what gets merged. Anything outside them (a full 1:1 map, multiplayer, extra cities) is likely to be closed with a link back to that file.

Open an issue before starting a large change so the approach can be agreed first.

## Useful contributions

- Bug reports against the `pa` tooling, with the command and output.
- Tests and fixes for any part of the `pa` code.
- Corrections to licence, attribution or provenance records.
- Local knowledge for the planned cities: landmarks, highway routes, roadhouses and fuel stops worth including.
- Notes from Build 42 testing that bear on the open engine questions in `.planning/`.

Playable map content is not accepted yet. The pilot has not chosen the scale and pipeline that content depends on.

## Setting up

Windows with Python 3.13:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m pytest
```

The default test run does not need the game or the external mapping tools. Do not commit game assets, map extracts, tool downloads or build output. `PINS.toml` records those by path and checksum only.

## Pull requests

- Link the issue, keep the change small, and add or update tests for logic changes.
- Every new input or third-party component needs a row in `ledger/licences.yaml`.
- Dependency changes go through `requirements.lock` with pinned versions.
- Tests must pass in CI before review.

Contributions are accepted under the repository's MIT licence.

## Conduct

Participation is covered by the [Code of Conduct](CODE_OF_CONDUCT.md). Report security problems as described in [SECURITY.md](SECURITY.md), not in public issues.
