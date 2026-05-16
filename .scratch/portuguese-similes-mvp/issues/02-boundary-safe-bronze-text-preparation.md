# Boundary-Safe Bronze Text Preparation

Status: complete

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Build the bronze preparation path for gzipped brWaC text. The slice should read the configured corpus input through Spark, treat `<END>` markers as hard paragraph/document boundaries, normalize whitespace for matching while preserving source text, assign source provenance, and write a bronze Parquet dataset that later extraction can consume without crossing segment boundaries.

## Acceptance criteria

- [x] Gzipped brWaC text can be read from the configured raw corpus input.
- [x] `<END>` markers are split or otherwise treated as hard segment boundaries before candidate extraction.
- [x] Empty segments are removed and repeated whitespace is collapsed for normalized text.
- [x] Original source text and lowercase accent-preserving match text are both available.
- [x] Bronze rows include source file identity, original input line identity, and segment identity after `<END>` splitting.
- [x] Bronze output is written as Spark Parquet.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/01-dockerized-pyspark-mvp-smoke-run.md
