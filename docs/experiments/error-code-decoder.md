# Error code decoder

**Status:** not started — good first issue.

**Idea:** `state_snapshots.error_code` and `.not_ready_code` (see `shared/schema.md`)
are small integers with no published meaning. Build a lookup table of code →
human-readable explanation + suggested fix, sourced and cited from community wikis
(see `docs/model-differences.md`'s note on why this isn't hardcoded in `normalize.py`),
and surface it in `ErrorLog.tsx` and/or a new `/errors/{code}` API field.

**Consumes:** `error_code`, `not_ready_code` from the core schema — works identically
on both model classes, no mapping-only fields needed.

**Suggested shape:** a small `error_codes.py` (or `.json`) module in `api/` with a
`{code: {message, suggested_fix, source_url}}` mapping, each entry cited to where
it was sourced from. Keep it separate from `normalize.py` so it can be corrected
independently of core normalization logic.
