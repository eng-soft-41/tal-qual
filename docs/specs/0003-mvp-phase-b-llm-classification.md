# Phase B — LLM Classification Sample

## Goal

Classify a stratified sample of refined Portuguese comparison candidates so the
project can estimate which candidates are figurative, literal, idiomatic, false
positive, or unclear.

Phase B is not part of the completed Spark MVP or Phase A structural
refinement. It is the next validation slice recommended by
`docs/context/mvp-phase-a-checkpoint.md`.

The phase should answer the remaining context question:

> Which candidates look figurative versus literal?

## Current Baseline

The completed MVP and Phase A runs produced:

```text
bronze corpus segments      4,673,057
silver candidates              58,797
refined Phase A candidates     58,797
```

Phase A is not a filter. The refined dataset preserves one row per silver
candidate and adds structural fields such as:

```text
nlp_refinement_scope
vehicle_phrase_nlp
vehicle_head
vehicle_head_lemma
vehicle_head_pos
structural_quality_bucket
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
vehicle_reject_reason
```

Phase B should use those fields to sample and interpret candidates, but it
should not modify the silver or refined Phase A datasets.

## Input

Primary input:

```text
data/gold/refined_candidates_nlp
```

Useful companion summaries:

```text
outputs/phase_a_scope_counts.csv
outputs/phase_a_quality_bucket_counts.csv
outputs/phase_a_top_clean_common_noun_heads.csv
outputs/phase_a_top_chartable_vehicle_heads.csv
outputs/phase_a_top_vehicle_heads_by_pattern.csv
outputs/phase_a_refinement_examples.csv
```

The old Phase B draft pointed at `data/silver/comparison_candidates.parquet`.
That is now stale. Classification should run on Phase A refined candidates so
the prompt can include structural vehicle fields and quality buckets.

## Model and Provider

Use OpenRouter through the official Python SDK.

Requested default model:

```text
deepseek/deepseek-v4-flash:free
```

OpenRouter lists this as a free model with a 256K context window. Because free
model availability and rate limits can change, the implementation should
preflight model availability through OpenRouter before running a batch. If the
requested free model is unavailable, fail clearly rather than silently switching
models.

Required environment variable:

```text
OPENROUTER_API_KEY
```

Never commit API keys. Local examples should assume the key is supplied through
the environment.

Recommended dependency:

```bash
uv add openrouter
```

The OpenRouter Python SDK is currently beta, so keep the integration isolated
behind a small module and avoid spreading SDK-specific code through notebooks.

## Agent Architecture

Follow the OpenRouter create-agent guidance at an implementation level:

- keep a standalone agent core independent of notebooks or UI;
- use environment variables for credentials;
- expose hook points for logging requests, responses, parse failures, retries,
  and cost/rate-limit metadata;
- keep any notebook or CLI as a thin orchestration layer;
- make the non-streaming path the default for batch classification;
- do not require a TUI for this project.

Recommended Python structure:

```text
src/tal_qual/llm_classification.py
  Classification labels, prompt construction, JSON parsing, validation,
  OpenRouter client wrapper, retry-safe single-row classification.

notebooks/05_phase_b_llm_classification.ipynb
  Stratified sample creation, dry-run preview, batch execution, summary charts.
```

The agent core should expose a small interface:

```text
classify_candidate(candidate: Mapping[str, Any]) -> ClassificationResult
```

It should use `OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY"))` and
`client.chat.send(...)` with the configured model.

## Sampling Strategy

Do not classify all `58,797` rows first.

Recommended first run:

```text
500 candidates
```

Recommended second run if quality is acceptable:

```text
1,000-2,000 candidates
```

Sample should be deterministic and stratified across:

```text
connector_family
pattern_type
nlp_refinement_scope
structural_quality_bucket
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
```

Prioritize enough rows from:

```text
clean_nominal_vehicle
proper_name_vehicle
role_or_classification_risk
pronoun_vehicle
clausal_or_verbal_continuation
not_in_first_slice_scope
```

The goal is not just to label clean examples. The sample should estimate which
structural buckets and connector patterns are actually useful for figurative
analysis.

## Labels

Use this label vocabulary:

```text
figurative_simile
literal_comparison
idiom_or_fixed_expression
non_comparison_false_positive
unclear
```

Definitions:

```text
figurative_simile
  The candidate expresses a figurative comparison or image, not merely factual
  similarity.

literal_comparison
  The candidate is a real comparison but appears literal, factual, taxonomic,
  numerical, role-based, or otherwise non-figurative.

idiom_or_fixed_expression
  The candidate is formulaic, idiomatic, proverbial, or culturally fixed enough
  that it should be inspected separately from productive simile formation.

non_comparison_false_positive
  The connector match does not function as a comparison candidate in context.

unclear
  The local context is insufficient, malformed, ambiguous, or the model should
  not guess.
```

## Prompt Contract

The prompt should be in Portuguese-aware English or Portuguese, but the output
must be strict JSON.

Each model call should include the fields most relevant for classification:

```text
candidate_id
candidate_full_text
text_before
matched_text
vehicle_raw
vehicle_normalized
connector_family
pattern_type
comparison_form
nlp_refinement_scope
vehicle_phrase_nlp
vehicle_head_lemma
vehicle_head_pos
structural_quality_bucket
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
vehicle_reject_reason
```

Required JSON response:

```json
{
  "label": "figurative_simile",
  "confidence": 0.82,
  "explanation_short": "The phrase compares speed to a lightning-like image.",
  "tenor": "the described subject, if recoverable",
  "ground": "the shared quality, if recoverable",
  "vehicle": "the comparison image, if recoverable",
  "needs_human_review": false
}
```

Validation rules:

- `label` must be one of the allowed labels.
- `confidence` must be a number from `0` to `1`.
- `explanation_short` must be one short sentence.
- `needs_human_review` should be true when label is `unclear`, confidence is
  low, JSON repair was needed, or the model output conflicts with structural
  fields.
- Missing optional `tenor`, `ground`, or `vehicle` values should be empty
  strings, not invented content.

## Output Contract

Write outputs separately from MVP and Phase A datasets.

Recommended durable output:

```text
data/gold/phase_b_llm_classifications
```

Recommended compact CSV summaries:

```text
outputs/phase_b_label_counts.csv
outputs/phase_b_label_counts_by_pattern.csv
outputs/phase_b_label_counts_by_quality_bucket.csv
outputs/phase_b_review_examples.csv
outputs/phase_b_classified_sample.csv
```

Recommended result fields:

```text
candidate_id
connector_family
pattern_type
nlp_refinement_scope
structural_quality_bucket
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
candidate_full_text
vehicle_raw
vehicle_phrase_nlp
vehicle_head_lemma
llm_model
llm_label
llm_confidence
llm_explanation_short
llm_tenor
llm_ground
llm_vehicle
needs_human_review
classification_run_id
classified_at
raw_response_json
parse_status
error_message
```

## Cost and Rate-Limit Policy

The requested model is free on OpenRouter at the time of this spec update, but
free models still have availability and rate-limit constraints. Phase B should
therefore be resumable and should persist partial results after each candidate
or small batch.

Implementation requirements:

- skip candidates that already have a successful classification for the current
  `classification_run_id`;
- write parse failures with `parse_status` and `error_message`;
- support a dry-run mode that builds prompts without calling the API;
- support `max_rows` for capped runs;
- record model id and provider response metadata when available;
- avoid concurrent calls until rate limits are understood.

## Test Steps

1. Build a deterministic stratified sample from
   `data/gold/refined_candidates_nlp`.
2. Preview prompts in dry-run mode.
3. Classify a tiny smoke sample, such as 10 candidates.
4. Validate JSON parsing and allowed labels.
5. Manually inspect the smoke output.
6. Run the first real sample, starting around 500 candidates.
7. Summarize label distribution by connector, pattern type, and Structural
   Quality Bucket.
8. Decide whether a larger 1,000-2,000 row sample is justified.

## Success Criteria

Phase B is useful if:

- it estimates figurative versus literal proportions on a defensible sample;
- labels are consistent enough after manual spot-checking;
- it reveals which connector patterns and quality buckets produce the best
  figurative candidates;
- it shows whether Phase A clean/chartable flags correlate with semantic
  usefulness;
- it produces compact outputs that can support a future visualization or
  presentation section;
- cost, rate limits, and operational complexity remain acceptable.

## Non-Goals

- Do not classify all 58,797 candidates as the first run.
- Do not mutate `data/silver/comparison_candidates`.
- Do not mutate `data/gold/refined_candidates_nlp`.
- Do not treat model labels as ground truth without human spot checks.
- Do not build an interactive review UI in this slice.
- Do not use LLM output to rewrite Phase A structural fields.

## Presentation Value

Phase B should be presented as a second-pass review experiment:

> Spark handles corpus-scale extraction, Phase A performs deterministic
> structural refinement, and Phase B uses an LLM on a sampled candidate set to
> estimate semantic quality and guide future visualization.

This preserves the project's careful language while finally addressing the
remaining figurative-versus-literal question from the original adaptation
context.
