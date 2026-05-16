# Phase A — NLP Refinement Layer

## Goal

Build a post-Spark NLP refinement layer that turns silver comparison candidates
into more analyzable linguistic units.

Phase A does not replace the MVP extraction pipeline. It reads the existing
silver candidate dataset, preserves silver candidate identity, and adds NLP
fields for vehicle structure, structural quality, and chart eligibility.

The first implementation slice focuses on vehicle structure refinement. Ground
adjective extraction and LLM classification remain downstream work after
vehicle fields are stable.

## Non-Goals

- Do not mutate or replace `data/silver/comparison_candidates`.
- Do not classify candidates as figurative or literal.
- Do not use an LLM in Phase A.
- Do not build a frontend app.
- Do not require Spark NLP unless a later class/project constraint demands it.
- Do not treat right-context strings as final semantic vehicles.

## Input

Primary input:

```text
data/silver/comparison_candidates
```

The input is the one-shard silver Parquet output from the MVP.

Phase A should support two run tiers:

```text
sample_debug
one_shard_refined
```

`sample_debug` uses a deterministic, pattern-stratified sample for fast rule
tuning and notebook inspection. `one_shard_refined` processes all silver
candidates from the validated one-shard run and is required for final Phase A
acceptance.

## NLP Tooling

Default implementation path:

```text
spaCy Portuguese
```

Use spaCy after Spark has reduced the corpus to candidate rows. Spark remains
the corpus-scale extraction engine; spaCy refines the smaller silver candidate
dataset.

NLTK is too shallow for head extraction. Spark NLP may be evaluated later if a
Spark-native NLP layer becomes a project requirement, but it should not be the
first implementation path.

## Parse Text

For the first vehicle-refinement slice, parse a controlled text window:

```text
nlp_parse_text = matched_text + " " + vehicle_raw
```

Vehicle extraction should select tokens after the matched connector phrase. Do
not parse only `vehicle_raw`, because that loses article and connector cues. Do
not parse the full `candidate_full_text` in the first slice, because left
context can add ambiguity before ground extraction exists.

If ground adjective extraction is later added, Phase A may introduce a separate
parse window with a short left-context tail.

## Refinement Scopes

Every silver row should be carried forward and assigned an
`nlp_refinement_scope`.

First-slice vehicle extraction targets:

```text
primary_nominal_article
primary_nominal_bare
```

Scope mapping:

```text
primary_nominal_article
  como_article
  feito_article
  parecer_article
  igual_article
  igualzinho_article

primary_nominal_bare
  que_nem_bare
  tal_qual_bare

clausal
  como_se

prepositional
  igual_preposition
  igualzinho_preposition
```

`primary_nominal_bare` candidates are first-slice targets, but should be
reported separately from article-gated candidates because their right side has
weaker syntactic cues.

## Vehicle Extraction Strategy

Use an inspectable hybrid strategy:

1. Prefer spaCy noun chunks that begin after the connector span.
2. Fallback to a POS-based span around the first noun-like token after the
   connector.
3. Use dependency head information when available to identify the vehicle head.
4. If no noun-like token is found, assign a structural quality bucket such as
   `clausal_or_verbal_continuation`, `empty_vehicle`, or `parser_uncertain`.

Core vehicle fields:

```text
vehicle_phrase_nlp
vehicle_head
vehicle_head_lemma
vehicle_head_pos
vehicle_phrase_length_tokens
vehicle_extraction_confidence
```

The full phrase is for examples and qualitative inspection. The head lemma is
the preferred aggregation key for vehicle-frequency charts.

## Structural Quality Buckets

Phase A should add deterministic structural labels, not figurative/literal
labels.

Initial bucket vocabulary:

```text
clean_nominal_vehicle
pronoun_vehicle
proper_name_vehicle
numeric_vehicle
empty_vehicle
clausal_or_verbal_continuation
overly_long_vehicle_phrase
url_or_symbol_noise
role_or_classification_risk
parser_uncertain
not_in_first_slice_scope
```

These buckets make obvious quality differences visible while leaving semantic
classification to a later phase.

## Chart Eligibility

Use two eligibility flags rather than one broad "aggregate eligible" flag:

```text
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
```

`vehicle_is_clean_common_noun` is conservative:

```text
true when:
  vehicle_head_pos == NOUN
  vehicle_head_lemma is not empty
  vehicle_phrase_length_tokens is within the short-phrase threshold
  structural_quality_bucket == clean_nominal_vehicle
```

`vehicle_is_chartable_vehicle` is broader:

```text
true for:
  clean common-noun vehicles
  selected proper-name vehicles

false for:
  pronouns
  numerals
  empty heads
  URL-like or symbol-heavy spans
  verbal or clausal continuations
  overly long phrases
```

This gives the project both a conservative noun-only chart and a broader
exploratory vehicle chart.

## Output Contract

Write the durable refined dataset as Parquet:

```text
data/gold/refined_candidates_nlp
```

One row per silver candidate. Preserve the core silver fields:

```text
candidate_id
source_file
original_line_id
segment_id
connector_family
pattern_type
comparison_form
matched_text
text_before
vehicle_raw
vehicle_normalized
candidate_full_text
char_start
char_end
```

Add Phase A fields:

```text
nlp_refinement_scope
nlp_parse_text
vehicle_phrase_nlp
vehicle_head
vehicle_head_lemma
vehicle_head_pos
vehicle_phrase_length_tokens
vehicle_extraction_confidence
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
vehicle_reject_reason
structural_quality_bucket
nlp_model_name
nlp_model_version
```

Write compact CSV summaries under `outputs/`:

```text
outputs/phase_a_scope_counts.csv
outputs/phase_a_quality_bucket_counts.csv
outputs/phase_a_top_clean_common_noun_heads.csv
outputs/phase_a_top_chartable_vehicle_heads.csv
outputs/phase_a_top_vehicle_heads_by_pattern.csv
outputs/phase_a_refinement_examples.csv
```

## Phase A Validation Notebook

Use the Phase A notebook for validation and presentation:

```text
notebooks/04_phase_a_validation.ipynb
```

The notebook should show:

- before/after top vehicles: `vehicle_normalized` versus `vehicle_head_lemma`;
- counts by `nlp_refinement_scope`;
- counts by `structural_quality_bucket`;
- clean common-noun vehicle heads;
- broader chartable vehicle heads;
- examples by `pattern_type`, `nlp_refinement_scope`, and
  `structural_quality_bucket`;
- side-by-side inspection columns:

```text
candidate_full_text
pattern_type
vehicle_raw
vehicle_phrase_nlp
vehicle_head_lemma
vehicle_head_pos
structural_quality_bucket
vehicle_reject_reason
```

The notebook is the validation and storytelling surface. The Parquet and CSV
outputs are the durable data contract for future phases.

To run the notebook in the Dockerized PySpark runtime, set
`TAL_QUAL_PHASE_A_TIER=sample_debug` for fast inspection or
`TAL_QUAL_PHASE_A_TIER=one_shard_refined` for the full one-shard acceptance
tier. The notebook writes or loads `data/gold/refined_candidates_nlp`, writes
the Phase A CSV summaries, and rejects stale refined outputs created without
the active spaCy parser model.

## Full One-Shard Validation Results

The completed `one_shard_refined` validation run used parser model
`core_news_sm 3.8.0`, ran through `notebooks/04_phase_a_validation.ipynb`, and
preserved one row per silver candidate:

```text
silver candidate rows   58,797
refined candidate rows  58,797
```

Counts by `nlp_refinement_scope`:

```text
primary_nominal_article    36,241
clausal                    14,723
primary_nominal_bare        4,520
prepositional               3,313
```

Counts by `structural_quality_bucket`:

```text
clean_nominal_vehicle          27,926
not_in_first_slice_scope       18,036
url_or_symbol_noise             4,488
role_or_classification_risk     3,706
pronoun_vehicle                 2,387
proper_name_vehicle               957
clausal_or_verbal_continuation    798
overly_long_vehicle_phrase        408
empty_vehicle                      57
numeric_vehicle                    34
```

Top clean common-noun heads included `forma`, `espécie`, `pessoa`, `homem`,
`alternativa`, `processo`, `sistema`, `meio`, `opção`, and `empresa`.
Chartable vehicle-head results were nearly identical at the top because the
full run found relatively few proper-name vehicles compared with common nouns.

The validation should be interpreted as structural evidence only. It shows that
Phase A can preserve row cardinality and create cleaner vehicle-head rankings,
but it does not decide whether candidates are figurative or literal. The full
run also exposed follow-up parser-quality cleanup candidates such as
quote-prefixed clean-ranking phrases, unhelpful noun-chunk heads, and
boilerplate-like web text.

## Success Criteria

Phase A is useful if:

- all silver candidates are preserved in `data/gold/refined_candidates_nlp`;
- first-slice target scopes produce inspectable vehicle phrase and head fields;
- clausal and prepositional patterns no longer dominate default noun-vehicle
  charts;
- quality bucket counts expose obvious noise categories;
- common-noun and chartable-vehicle charts are materially cleaner than the MVP
  `vehicle_normalized` rankings;
- the validation notebook demonstrates the before/after improvement with
  examples;
- the approach remains simple enough to explain as post-Spark refinement.

## Known Risks

- spaCy Portuguese parses may be wrong on noisy web text.
- Bare connectors such as `que nem` and `tal qual` may require weaker confidence
  than article-gated patterns.
- Proper-name vehicles can be interesting but may pollute conservative noun
  rankings.
- Some classification/role uses may look syntactically nominal, such as
  `trabalha como advogado` or `conhecido como X`.
- Ground adjective extraction remains unresolved until vehicle refinement is
  stable.

## Implementation Slices

1. Add Phase A output paths, schema, and run-tier helpers.
2. Add spaCy-based vehicle structure refinement for `primary_nominal_article`
   and `primary_nominal_bare` scopes.
3. Add structural quality buckets and chart eligibility flags.
4. Write refined Parquet and compact CSV summaries.
5. Add the Phase A validation notebook.
6. Add focused unit tests for scope mapping, parse text construction, vehicle
   head extraction, eligibility flags, and quality buckets.
