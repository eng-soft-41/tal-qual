# Phase A Aggregation Outputs

Status: ready-for-agent

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Produce compact Phase A CSV outputs from the Refined Candidate Dataset. The completed slice should make the refinement results inspectable without opening Parquet directly and should support before/after evaluation of vehicle quality.

The outputs should summarize refinement scopes, Structural Quality Buckets, conservative common-noun vehicle heads, broader Chartable Vehicle heads, vehicle heads by pattern, and representative side-by-side refinement examples.

## Acceptance criteria

- [ ] Scope count CSV output is written from the Refined Candidate Dataset.
- [ ] Structural Quality Bucket count CSV output is written from the Refined Candidate Dataset.
- [ ] Top Clean Common-Noun Vehicle head CSV output is written.
- [ ] Top Chartable Vehicle head CSV output is written.
- [ ] Top vehicle heads by pattern type CSV output is written.
- [ ] Refinement examples CSV output includes side-by-side raw and refined vehicle fields.
- [ ] Aggregations use Vehicle Head lemma as the default refined vehicle aggregation key.
- [ ] Outputs are deterministic enough for repeatable inspection.
- [ ] Focused tests cover aggregation behavior on tiny refined candidate samples.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/03-structural-quality-buckets-and-vehicle-eligibility.md
