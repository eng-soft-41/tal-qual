# Vehicle Normalization and Gold Aggregations

Status: complete

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Turn silver candidates into inspectable MVP outputs. This slice should add simple vehicle normalization, persist the full silver candidate dataset in Parquet, and produce compact CSV outputs for candidate sampling, connector counts, pattern counts, top vehicles, and stratified sample examples.

## Acceptance criteria

- [x] `vehicle_normalized` is derived with lowercase, whitespace cleanup, and surrounding punctuation trimming.
- [x] Leading Portuguese articles are preserved in `vehicle_normalized` by default.
- [x] Full silver candidate output is written as Spark Parquet.
- [x] A deterministic candidate sample CSV of up to 5,000 rows is produced.
- [x] Connector-family and pattern-type count CSVs are produced.
- [x] Top vehicle CSVs are produced globally, by connector family, and by pattern type.
- [x] Vehicle count outputs include occurrence counts and, where useful, distinct candidate text counts.
- [x] Sample examples include up to 20 deterministic examples per pattern type.
- [x] Sample examples deduplicate repeated candidate text before selection while silver preserves all occurrences.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/03-narrow-connector-candidate-extraction.md
