# Narrow Connector Candidate Extraction

Status: ready-for-agent

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Implement silver candidate extraction over prepared bronze segments using only the agreed high-value narrow connector patterns. The completed slice should emit one row per connector match with exact matched text, connector family, pattern type, comparison form, capped local context, right-context vehicle text, deterministic candidate identity, and clear offsets in normalized segment text.

## Acceptance criteria

- [ ] Extraction emits one silver row per connector match, including multiple matches in the same segment.
- [ ] No generic `como` pattern is included.
- [ ] Article-gated `como`, clausal `como se`, bare `que nem`, bare `tal qual`, `parecer` article variants, agreement-aware `feito` article variants, and `igual`/`igualzinho` subtypes are implemented.
- [ ] Each row includes `connector_family`, `pattern_type`, `comparison_form`, and exact `matched_text`.
- [ ] `vehicle_raw` starts after the exact matched connector phrase.
- [ ] `text_before` is capped at 80 characters and `candidate_full_text` uses compact local context.
- [ ] Right context stops at punctuation, segment boundary, or 120 characters.
- [ ] `candidate_id` is deterministic from provenance, offsets, pattern type, and matched text.
- [ ] `char_start` and `char_end` are zero-based end-exclusive offsets in normalized segment text.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/02-boundary-safe-bronze-text-preparation.md

