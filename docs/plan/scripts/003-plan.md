# 003-plan — Isolate the save engine

## Objective

Protect binary behavior while preventing application features from depending on codec implementation details.

## Tasks

- Define application-owned interfaces for inspect, load, document access, and save.
- Keep compression, GVAS, property dispatch, rawdata codecs, unknown properties, and trailing bytes behind that boundary.
- Separate codec errors from application and storage errors.
- Add roundtrip, byte-preservation, trailer, compression, Booth, Guild, and opaque-property characterization tests.
- Do not internally reorganize `palsav` until these tests pass.

## Files and areas

`src/palsav/core.py`, `src/palsav/io.py`, `src/palsav/gvas.py`, `src/palsav/archive.py`, `src/palsav/paltypes.py`, `src/palsav/palobject.py`, `src/palsav/rawdata/`, `src/palsav/palooz/`, and a new adapter boundary outside `palsav`.

## Dependencies

`001-plan`, `002-plan`.

## Acceptance

Application code can load and save through the boundary while all characterized binary and preservation behavior remains unchanged.

