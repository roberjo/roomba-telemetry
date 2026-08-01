# Experiments

Each experiment from PROJECT.md §5 gets a write-up here (`<name>.md`) plus, if it
needs code, an optional `experiments/<name>/` directory at the repo root — kept
separate so the core `collector`/`api`/`web` stay uncluttered (PROJECT.md §4 Phase 6).

A write-up should cover: what it does, which normalized fields it consumes
(link to `shared/schema.md`), and whether it needs the mapping-only fields (and
therefore only works for 900-series vSLAM robots).

Start here if you're picking up a "Small / weekend-scale" idea from PROJECT.md §5 —
they're the best first contributions since they're additive and don't touch the
core collector/API.
