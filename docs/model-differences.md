# 600-series vs. 900-series (vSLAM) payload differences

This is the deep-dive PROJECT.md §5 calls for — a genuinely useful reference since
iRobot doesn't publish the local API. It's based on community reverse-engineering
(dorita980, roomba980-python, and their issue trackers) plus the fixtures in
`collector/tests/fixtures/`. Treat specifics as best-effort and firmware-dependent;
file an issue with a raw payload capture if your robot disagrees.

## Fields present on both model classes

`batPct`, `bin.present`, `bin.full`, `cleanMissionStatus.{cycle,phase,error,notReady,
mssnM,sqft,initiator}`, `signal.{rssi,snr}`, `lastCommand`.

These map directly to the "core" fields in `shared/schema.md`. `mssnM`/`sqft` are
coarser on 600-series robots — they lack the vSLAM camera used for precise room
coverage estimation, so area is dead-reckoned from wheel odometry instead.

## Fields unique to mapping-capable (vSLAM) models

`pose.theta` and `pose.point.{x,y}` — the robot's estimated position/heading
relative to its dock, in millimeters/degrees. Only present while the camera has a
localization fix; expect gaps around the start of a mission and while docked.

Mapping models also expose room-level map data and room-by-room stats through a
separate, less-well-documented channel than the plain state topic — out of scope
for the current schema (`shared/schema.md`) until Phase 6's "cleaning heatmap"
experiment needs it (PROJECT.md §5).

## Error / not-ready codes

`cleanMissionStatus.error` and `.notReady` are small integers whose meanings are
not published by iRobot and vary somewhat by firmware/region. This project
deliberately does *not* hardcode a code → message table in `normalize.py` — that
belongs in the "error code decoder" experiment (PROJECT.md §5, small/weekend-scale),
sourced and cited from community wikis, so it can be corrected independently of the
core normalization logic. If you're picking that up, `docs/experiments/error-code-decoder.md`
is the place for it.

## Firmware drift

Both the discovery/pairing handshake (`collector/collector/pairing.py`) and the
state schema have changed across firmware versions in the past. If normalization
throws unexpected-shape errors or fields silently show up as `null` that you know
your robot reports, capture a raw payload (`collector`'s raw JSONL logger, Phase 0)
and add it as a new fixture rather than guessing.
