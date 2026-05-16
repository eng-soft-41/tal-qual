# Phase A Documentation Alignment

Status: complete

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Align project documentation with the completed Phase A NLP Refinement Layer. The completed slice should explain how Phase A fits after the Spark MVP, how to run the refinement workflow and validation notebook, where outputs are written, how to interpret the new fields, and which limitations still apply.

The documentation should preserve careful project language: Phase A produces structural refinement and chartable vehicle fields, not final simile detection or figurative/literal classification.

## Acceptance criteria

- [x] Documentation explains Phase A as a post-Spark NLP Refinement Layer.
- [x] Documentation explains how to run the sample-debug and one-shard refined tiers.
- [x] Documentation lists the Refined Candidate Dataset output and Phase A CSV outputs.
- [x] Documentation defines the main new fields, including refinement scope, Vehicle Phrase, Vehicle Head, Structural Quality Bucket, Clean Common-Noun Vehicle, and Chartable Vehicle.
- [x] Documentation explains how to open and interpret the Phase A Validation Notebook.
- [x] Documentation records full one-shard refined validation results.
- [x] Documentation clearly states that Phase A does not classify figurative versus literal meaning.
- [x] Documentation keeps ground adjective extraction and LLM classification as downstream work.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/06-one-shard-refined-run-validation.md

## Completion notes

- `README.md` now documents Phase A as a post-Spark NLP Refinement Layer, the two run tiers, the validation notebook, the refined Parquet output, Phase A CSV outputs, key fields, one-shard validation counts, and limitations.
- `docs/specs/0002-mvp-phase-A-nlp-filter.md` now matches the implemented notebook filename and CSV path names, and records the full one-shard validation results.
- Added a focused documentation test so future edits keep the public docs aligned with the implemented Phase A contract.
