# Vehicle Normalization and Gold Aggregations

Status: ready-for-agent

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Turn silver candidates into inspectable MVP outputs. This slice should add simple vehicle normalization, persist the full silver candidate dataset in Parquet, and produce compact CSV outputs for candidate sampling, connector counts, pattern counts, top vehicles, and stratified sample examples.

## Acceptance criteria

- [ ] `vehicle_normalized` is derived with lowercase, whitespace cleanup, and surrounding punctuation trimming.
- [ ] Leading Portuguese articles are preserved in `vehicle_normalized` by default.
- [ ] Full silver candidate output is written as Spark Parquet.
- [ ] A deterministic candidate sample CSV of up to 5,000 rows is produced.
- [ ] Connector-family and pattern-type count CSVs are produced.
- [ ] Top vehicle CSVs are produced globally, by connector family, and by pattern type.
- [ ] Vehicle count outputs include occurrence counts and, where useful, distinct candidate text counts.
- [ ] Sample examples include up to 20 deterministic examples per pattern type.
- [ ] Sample examples deduplicate repeated candidate text before selection while silver preserves all occurrences.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/03-narrow-connector-candidate-extraction.md

