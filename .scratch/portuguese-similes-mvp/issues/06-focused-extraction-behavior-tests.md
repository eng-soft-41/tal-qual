# Focused Extraction Behavior Tests

Status: complete

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Add lightweight tests for the externally visible behavior of the extraction logic. These tests should protect the agreed extraction contract without becoming a blocker for exploratory Spark work or requiring the real brWaC shard.

## Acceptance criteria

- [x] Tests cover `<END>` boundary handling so candidates do not cross segment boundaries.
- [x] Tests cover one-row-per-match behavior for multiple matches in one segment.
- [x] Tests verify that generic `como` is excluded while agreed narrow `como` variants are included.
- [x] Tests cover agreed `parecer`, `feito`, `igual`, `igualzinho`, `que nem`, and `tal qual` variants.
- [x] Tests verify that `vehicle_raw` starts after exact `matched_text`.
- [x] Tests cover left-context and right-context caps.
- [x] Tests cover simple `vehicle_normalized` behavior while preserving leading articles.
- [x] Tests verify deterministic candidate identity inputs or stable IDs for representative examples.
- [x] Tests use small sample strings or tiny temporary data, not the real brWaC shard.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/03-narrow-connector-candidate-extraction.md

## Notes

- Added focused in-memory behavior coverage around bronze `<END>` splitting plus silver extraction.
- Expanded connector variant tests for the agreed narrow `como`, `parecer`, `feito`, `igual`, `igualzinho`, `que nem`, and `tal qual` forms.
- Fixed the explicit article regexes so `uns` variants are matched for `como`, `igual`, and `igualzinho`.
