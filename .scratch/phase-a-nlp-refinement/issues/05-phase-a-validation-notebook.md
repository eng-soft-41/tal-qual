# Phase A Validation Notebook

Status: complete

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Add the Phase A Validation Notebook as the inspection and presentation surface for the NLP Refinement Layer. The notebook should run the Phase A workflow or load its durable outputs, then demonstrate whether Vehicle Structure Refinement improves the data compared with the MVP `vehicle_normalized` rankings.

The notebook should make the refinement legible through tables and simple charts rather than becoming the owner of extraction logic.

## Acceptance criteria

- [x] The notebook can run in the project’s expected local workflow and load Phase A refined outputs.
- [x] The notebook shows before/after top vehicles using MVP `vehicle_normalized` and refined Vehicle Head lemma.
- [x] The notebook shows counts by `nlp_refinement_scope`.
- [x] The notebook shows counts by Structural Quality Bucket.
- [x] The notebook shows conservative Clean Common-Noun Vehicle rankings.
- [x] The notebook shows broader Chartable Vehicle rankings.
- [x] The notebook displays side-by-side examples with candidate text, pattern type, raw vehicle, Vehicle Phrase, Vehicle Head lemma, Vehicle Head POS, Structural Quality Bucket, and reject reason.
- [x] The notebook communicates that Phase A is structural refinement, not figurative/literal classification.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/04-phase-a-aggregation-outputs.md
