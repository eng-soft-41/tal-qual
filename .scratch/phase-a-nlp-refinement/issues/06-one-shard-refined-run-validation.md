# One-Shard Refined Run Validation

Status: ready-for-agent

## Parent

.scratch/phase-a-nlp-refinement/PRD.md

## What to build

Validate Phase A against the full one-shard silver candidate output. The completed slice should run the `one_shard_refined` tier, produce the durable Refined Candidate Dataset and CSV summaries, inspect the Phase A Validation Notebook outputs, and record observed counts, quality signals, limitations, and any follow-up risks.

This issue proves that Phase A works end to end over the MVP output rather than only on a small debug sample.

## Acceptance criteria

- [ ] The `one_shard_refined` tier runs against the validated one-shard silver candidate dataset.
- [ ] Full refined Parquet output is produced with one row per silver candidate.
- [ ] Phase A CSV summaries are produced from the full refined dataset.
- [ ] The Phase A Validation Notebook can inspect the full-run outputs.
- [ ] Observed counts by refinement scope are recorded.
- [ ] Observed counts by Structural Quality Bucket are recorded.
- [ ] Top common-noun and chartable vehicle-head examples are recorded.
- [ ] Known limitations from the full run are documented without overclaiming figurative/literal classification.
- [ ] Parser-quality cleanup candidates are recorded for `.scratch/phase-a-nlp-refinement/issues/08-phase-a-refinement-quality-cleanup.md`.

## Blocked by

- .scratch/phase-a-nlp-refinement/issues/05-phase-a-validation-notebook.md
