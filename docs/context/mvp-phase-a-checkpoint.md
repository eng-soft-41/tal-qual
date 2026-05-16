# MVP + Phase A Checkpoint

Date: 2026-05-16

This checkpoint records the project state after completing both the Portuguese
Simile Candidate Explorer MVP PRD and the Phase A NLP Refinement Layer PRD.

## Current Status

The project has moved past a skeleton prototype. It now has a validated
Spark-based extraction pipeline over one full brWaC shard and a post-Spark NLP
refinement layer that preserves silver candidate identity while adding
structural vehicle fields.

The defensible project framing is:

> A Spark-based exploratory pipeline for extracting and structurally refining
> explicit comparison candidates in Portuguese text.

Avoid claiming that the project is a final simile detector or that it classifies
figurative versus literal meaning.

## Validated Scale

The one-shard MVP and Phase A runs produced:

```text
bronze corpus segments      4,673,057
silver candidates              58,797
refined Phase A candidates     58,797
```

Phase A preserves one refined row per silver candidate.

## Main Artifacts

Notebook responsibilities:

```text
notebooks/01_pyspark_smoke_run.ipynb
  Spark/runtime sanity check on a tiny sample.

notebooks/02_bronze_text_preparation.ipynb
  Raw brWaC text to boundary-safe bronze segments.

notebooks/03_one_shard_end_to_end_validation.ipynb
  Full MVP extraction validation.

notebooks/03-1_one_shard_materialized_validation.ipynb
  Lower-memory/materialized variant of the one-shard MVP validation.

notebooks/04_phase_a_validation.ipynb
  Phase A before/after inspection using refined vehicle-head fields.
```

Durable output families:

```text
data/bronze/brwac_segments
data/silver/comparison_candidates
data/gold/refined_candidates_nlp
outputs/*.csv
```

Generated data and outputs are local/ignored artifacts, not source files.

## MVP Findings

The Spark MVP answered the first-order feasibility questions.

Connector-family counts from the one-shard run:

```text
como          47,913
que_nem        3,912
igual          3,268
parecer        1,651
feito          1,340
tal_qual         608
igualzinho       105
```

Pattern-type counts:

```text
como_article              33,190
como_se                   14,723
que_nem_bare               3,912
igual_preposition          3,210
parecer_article            1,651
feito_article              1,340
tal_qual_bare                608
igualzinho_preposition       103
igual_article                 58
igualzinho_article             2
```

The central MVP learning is that connector extraction works at useful scale,
but raw right-context vehicles are too noisy for final analysis. Top raw
`vehicle_normalized` values included discourse or clausal continuations such as
`todo`, `sabe`, `vê`, `não bastasse`, numbers, pronouns, and empty strings.

That result validates the need for Phase A rather than undermining the MVP: the
Spark layer finds candidate rows; the NLP layer makes the reduced candidate set
more analyzable.

## Phase A Findings

Phase A runs spaCy Portuguese after Spark reduction and adds structural vehicle
fields, including:

```text
nlp_refinement_scope
vehicle_phrase_nlp
vehicle_head
vehicle_head_lemma
vehicle_head_pos
structural_quality_bucket
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
```

Counts by refinement scope:

```text
primary_nominal_article    36,241
clausal                    14,723
primary_nominal_bare        4,520
prepositional               3,313
```

Post-cleanup Structural Quality Bucket counts:

```text
clean_nominal_vehicle          27,606
not_in_first_slice_scope       18,036
url_or_symbol_noise             4,700
role_or_classification_risk     3,672
pronoun_vehicle                 2,383
proper_name_vehicle               948
clausal_or_verbal_continuation    793
overly_long_vehicle_phrase        398
numeric_vehicle                   104
parser_uncertain                  100
empty_vehicle                      57
```

Top clean common-noun vehicle heads include:

```text
forma
espécie
pessoa
homem
alternativa
processo
sistema
meio
opção
empresa
criança
ferramenta
problema
luva
jogo
```

These are cleaner analysis units than raw right-context strings, but they are
still structural heads, not confirmed figurative vehicles.

## Questions From The Original Context

Current answers:

```text
Can we extract enough Portuguese comparison candidates?
  Yes. One shard produced 58,797 candidates.

Which connectors are most common?
  Yes. como dominates; que_nem and igual are the next largest families.

Which comparison vehicles appear most often?
  Partially yes. Raw MVP vehicles are noisy; Phase A refined vehicle heads are
  much better for ranking and visualization.

Which candidates look figurative versus literal?
  Not answered yet. The project intentionally has not done semantic
  classification.

Which patterns are promising for interactive visualizations?
  Yes. como_article is the strongest volume source. que_nem_bare is useful but
  noisier. Refined clean/chartable vehicle-head rankings are suitable for
  first visualization datasets.

Can the pipeline satisfy the class requirement of using Apache Spark?
  Yes. Spark handles ingestion, segmentation, extraction, aggregation, and
  Parquet/CSV output over a real corpus shard.
```

## How Close The Project Is

For the original MVP goal, the project is essentially complete.

For a broader Portuguese simile-analysis project, the project is roughly at
the midpoint:

Done:

```text
Spark extraction over real corpus data
connector frequency analysis
candidate dataset
raw vehicle summaries
NLP vehicle-head refinement
quality buckets
clean/chartable vehicle summaries
validation notebook
clear limitations
```

Not done:

```text
figurative versus literal classification
human or LLM review sample
tenor and ground extraction
interactive visualization
multi-shard or full-corpus scaling
presentation-ready narrative charts
```

## Recommended Next Slice

The next highest-value slice is a small classification or review phase, not
more extraction.

Use a stratified sample from the refined outputs and label candidates as:

```text
figurative_simile
literal_comparison
idiom_or_fixed_expression
non_comparison_false_positive
unclear
```

This would answer the biggest remaining context question: which candidates are
actually figurative. It would also estimate precision by connector family,
pattern type, and Structural Quality Bucket before investing in a polished
visualization.

## Presentation Guidance

Recommended story:

1. Spark processed a real Portuguese web-corpus shard.
2. Narrow connector rules produced a large explicit-comparison candidate pool.
3. Raw right-context vehicles were useful for feasibility but too noisy for
   analysis.
4. Phase A refined the candidate set structurally without deleting rows or
   overclaiming semantic meaning.
5. The next phase should classify a sample to estimate figurative precision and
   guide visualizations.

Do not present Phase A as a figurative/literal classifier. Present it as a
structural refinement layer that makes later human or LLM classification more
defensible.
