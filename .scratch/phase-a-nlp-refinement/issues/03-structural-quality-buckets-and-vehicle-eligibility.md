# Structural Quality Buckets and Vehicle Eligibility

Status: complete

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Add deterministic Structural Quality Buckets and vehicle chart eligibility flags to the Refined Candidate Dataset. The completed slice should distinguish clean nominal vehicles from pronouns, proper names, numerals, empty spans, clausal or verbal continuations, overly long phrases, URL or symbol noise, parser uncertainty, non-target scopes, and role or classification risk.

This slice should not classify candidates as figurative or literal. It should provide structural signals and reject reasons that make later analysis and charting more defensible.

## Acceptance criteria

- [x] Each refined row receives a `structural_quality_bucket`.
- [x] Each refined row receives a `vehicle_reject_reason` when it is not suitable for a default chart.
- [x] Pronoun, proper-name, numeric, empty, clausal/verbal, overly long, URL/symbol, parser-uncertain, and not-in-first-slice cases are represented in the bucket vocabulary.
- [x] Role or classification risk is detected heuristically and marked without deleting the row.
- [x] Clean Common-Noun Vehicle eligibility is stricter than Chartable Vehicle eligibility.
- [x] Proper-name vehicles can be preserved and chartable without being clean common-noun vehicles.
- [x] Pronouns, numerals, empty heads, URL-like spans, clausal/verbal continuations, and overly long phrases are excluded from default chart eligibility.
- [x] Focused tests cover each major bucket, both eligibility flags, and role/classification risk examples.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/02-vehicle-structure-refinement-first-slice.md
