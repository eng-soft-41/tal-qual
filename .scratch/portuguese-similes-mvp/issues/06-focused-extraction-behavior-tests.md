# Focused Extraction Behavior Tests

Status: ready-for-agent

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Add lightweight tests for the externally visible behavior of the extraction logic. These tests should protect the agreed extraction contract without becoming a blocker for exploratory Spark work or requiring the real brWaC shard.

## Acceptance criteria

- [ ] Tests cover `<END>` boundary handling so candidates do not cross segment boundaries.
- [ ] Tests cover one-row-per-match behavior for multiple matches in one segment.
- [ ] Tests verify that generic `como` is excluded while agreed narrow `como` variants are included.
- [ ] Tests cover agreed `parecer`, `feito`, `igual`, `igualzinho`, `que nem`, and `tal qual` variants.
- [ ] Tests verify that `vehicle_raw` starts after exact `matched_text`.
- [ ] Tests cover left-context and right-context caps.
- [ ] Tests cover simple `vehicle_normalized` behavior while preserving leading articles.
- [ ] Tests verify deterministic candidate identity inputs or stable IDs for representative examples.
- [ ] Tests use small sample strings or tiny temporary data, not the real brWaC shard.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/03-narrow-connector-candidate-extraction.md

