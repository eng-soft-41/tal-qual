# Phase A Documentation Alignment

Status: ready-for-agent

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Align project documentation with the completed Phase A NLP Refinement Layer. The completed slice should explain how Phase A fits after the Spark MVP, how to run the refinement workflow and validation notebook, where outputs are written, how to interpret the new fields, and which limitations still apply.

The documentation should preserve careful project language: Phase A produces structural refinement and chartable vehicle fields, not final simile detection or figurative/literal classification.

## Acceptance criteria

- [ ] Documentation explains Phase A as a post-Spark NLP Refinement Layer.
- [ ] Documentation explains how to run the sample-debug and one-shard refined tiers.
- [ ] Documentation lists the Refined Candidate Dataset output and Phase A CSV outputs.
- [ ] Documentation defines the main new fields, including refinement scope, Vehicle Phrase, Vehicle Head, Structural Quality Bucket, Clean Common-Noun Vehicle, and Chartable Vehicle.
- [ ] Documentation explains how to open and interpret the Phase A Validation Notebook.
- [ ] Documentation records full one-shard refined validation results.
- [ ] Documentation clearly states that Phase A does not classify figurative versus literal meaning.
- [ ] Documentation keeps ground adjective extraction and LLM classification as downstream work.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/06-one-shard-refined-run-validation.md
