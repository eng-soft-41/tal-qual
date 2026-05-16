# Scope-Labeled Refined Candidate Dataset

Status: ready-for-agent

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Create the first end-to-end tracer bullet for the NLP Refinement Layer. The completed slice should read the existing silver candidate output, preserve one row per Silver Candidate, assign an `nlp_refinement_scope`, construct a controlled NLP parse text, support a deterministic sample-debug run tier, and write a minimal Refined Candidate Dataset without mutating silver output.

This slice does not need to perform real vehicle head extraction yet. It establishes the downstream dataset shape and proves that Phase A can carry silver candidates forward with stable identity and scope metadata.

## Acceptance criteria

- [ ] The refinement workflow preserves Silver Candidate identity and one output row per input silver row.
- [ ] Core silver fields needed for traceability are preserved in the Refined Candidate Dataset.
- [ ] Each row receives an `nlp_refinement_scope` derived from `pattern_type`.
- [ ] Scope mapping covers primary nominal article, primary nominal bare, clausal, and prepositional candidates.
- [ ] Each row includes `nlp_parse_text` built from matched connector text plus the raw vehicle window.
- [ ] A deterministic `sample_debug` tier produces a pattern-stratified subset for fast inspection.
- [ ] A `one_shard_refined` tier can target the full silver candidate dataset.
- [ ] The minimal Refined Candidate Dataset is written as Parquet.
- [ ] Focused tests cover scope mapping, parse text construction, row preservation, and deterministic sampling behavior.

## Blocked by

None - can start immediately
