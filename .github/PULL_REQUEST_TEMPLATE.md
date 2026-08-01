## What does this change?

<!-- One or two sentences. Link any related issue with "Closes #123". -->

## Why?

<!-- What problem does this solve, or what's the motivation? -->

## How was this tested?

- [ ] `pytest collector/tests` passes
- [ ] `pytest api/tests` passes
- [ ] `npm run build && npm run lint` passes in `web/`
- [ ] Tested against a fixture (`scripts/replay.py`) and/or real hardware — note which

## Checklist

- [ ] If this adds/changes a normalized field, `shared/schema.md` is updated
- [ ] If this makes claims about the local API protocol, they're verified against
      a real payload or the current upstream reference (not just memory/old docs)
- [ ] Mapping-only fields/features are still optional and null-checked (see
      [PROJECT.md's design principles](../PROJECT.md#6-design-principles-for-contributors))
