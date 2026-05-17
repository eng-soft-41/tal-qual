# Dataset Expansion Experiments

## Goal

Find a low-complexity path to increase the Portuguese comparison dataset before
building the first WebApp visualizations.

The current full-corpus `Como-Article Ground/Vehicle Candidate` run produced
2,136 kept candidates. That is enough for a narrow cliche prototype, but too
small for a broader exploratory visualization.

This spec proposes three isolated experiments to run in separate notebooks over
one raw shard first, preferably `brwac-clean-1.txt.gz`. Each experiment should
answer:

- how many extra candidates it adds;
- whether the top pairs look visualizable;
- which false-positive family dominates;
- whether the idea is simple enough to promote into the main pipeline.

These experiments should not replace spec 0006 until reviewed.

## Non-Goals

- Do not run spaCy over the full bronze corpus.
- Do not build a general Portuguese simile parser.
- Do not merge all connector families into one output without preserving
  `pattern_type`.
- Do not optimize for recall if the review sample becomes mostly noise.

## Baseline

Use spec 0006 as the baseline:

```text
CURATED_GROUND como um/uma/uns/umas VEHICLE
```

One-shard baseline from the current run:

```text
Prefiltered bronze rows: 333
Spec-0006 candidates: 204
```

Full-corpus baseline:

```text
Spec-0006 candidates: 2,136
```

## Shared Experiment Contract

Each experiment should produce the same minimum review artifacts:

```text
outputs/experiments/<experiment_slug>/candidate_counts.csv
outputs/experiments/<experiment_slug>/ground_vehicle_counts.csv
outputs/experiments/<experiment_slug>/vehicle_counts.csv
outputs/experiments/<experiment_slug>/review_sample.csv
outputs/experiments/<experiment_slug>/quality_notes.md
```

Each candidate row should include:

```text
candidate_id
pattern_type
source_file
original_line_id
segment_id
connector_text
matched_text
candidate_full_text
text_before
ground_text
ground_lemma
ground_source
vehicle_text_raw
vehicle_text_clean
vehicle_head_clean
vehicle_tail_text
quality_label
quality_reason
needs_review
char_start
char_end
```

For exploratory runs, `quality_label` may be rule-based:

```text
keep
trimmed
review
reject
```

The important point is to preserve raw text and expose the cleanup decision.

## Experiment 1: Bare `como` With Curated Ground

### Hypothesis

Many high-value Portuguese comparisons omit the article:

```text
frio como gelo
forte como touro
rápido como raio
duro como pedra
leve como pluma
branco como neve
claro como água
```

Adding bare `como` after the same curated ground lists may increase volume
without a large implementation jump.

### Pattern

```text
CURATED_GROUND como VEHICLE
```

Exclude the existing article forms from this experiment, so it measures only
incremental value:

```text
como um
como uma
como uns
como umas
```

### Candidate Filter

Use a Spark native prefilter:

```text
\b(CURATED_GROUND)\s+como\s+(?!um\b|uma\b|uns\b|umas\b)
```

Then run Python extraction on the prefiltered rows.

### Vehicle Rules

Start with 1 to 4 tokens after `como`, stopping at punctuation or segment
boundary.

For the first pass, prefer a stricter vehicle boundary than spec 0006:

- keep one-token vehicles by default;
- allow `de/do/da` noun complements only up to 3 tokens;
- trim after finite verbs, pronouns, and clause-like tails;
- mark capitalized multi-token vehicles as `review`.

### Expected Upside

This should add canonical visual pairs that spec 0006 misses, especially
physical/object vehicles without articles.

### Main Risk

Bare `como` also introduces role and manner readings:

```text
trabalhar como profissional
agir como adulto
funcionar como sistema
```

Mitigation: start with quality adjectives only, then add salient verbs if the
review sample holds up.

### Promotion Criteria

Promote if one-shard results show:

- at least 2x the spec-0006 one-shard candidate count;
- at least 60% `keep` or `trimmed` in a 200-row review sample;
- top 30 pairs are mostly visualizable comparisons, not role/classification
  uses.

## Experiment 2: Colloquial Connectors `que nem` And `feito`

### Hypothesis

Brazilian Portuguese uses informal comparison connectors heavily:

```text
forte que nem touro
rápido que nem raio
duro feito pedra
leve feito pluma
corre feito louco
```

These may add culturally useful examples and diversify the visualization beyond
formal `como`.

### Pattern

```text
CURATED_GROUND que nem VEHICLE
CURATED_GROUND feito/feita/feitos/feitas VEHICLE
```

Start with the same curated grounds as spec 0006.

### Candidate Filter

Use a native Spark prefilter:

```text
\b(CURATED_GROUND)\s+(?:que\s+nem|feito|feita|feitos|feitas)\b
```

### Vehicle Rules

Use the same stricter vehicle cleanup as Experiment 1. These connectors often
take short vehicles, so one-token and two-token vehicles should be treated as
the preferred shape.

### Expected Upside

This may find more expressive examples than bare `como`, especially for
movement and behavior grounds:

```text
correr
voar
brilhar
trabalhar
```

### Main Risk

`feito` can be a participle or ordinary verb form, and `que nem` can occur in
messy informal text. False positives may be noisier than bare `como`.

Mitigation: require curated ground immediately before connector and reject rows
where `feito` is preceded by auxiliary/passive context.

### Promotion Criteria

Promote if one-shard results show:

- at least 25% incremental candidate gain over spec 0006;
- top pairs add new vehicle heads, not only duplicates of `luva` and `bomba`;
- review sample has a clearly separable false-positive pattern that rules can
  handle.

## Experiment 3: Broader Ground Window For Article `como`

### Hypothesis

The current extractor requires the ground to be the token immediately before
`como`. This misses common Portuguese structures where intensifiers, negation,
or modifiers intervene:

```text
tão leve como uma pluma
mais rápido como um raio
quase duro como uma pedra
bem forte como um touro
```

Keeping the same article connector but allowing a small left window may recover
good candidates with less connector complexity.

### Pattern

```text
GROUND_WINDOW como um/uma/uns/umas VEHICLE
```

Where `GROUND_WINDOW` is the last curated ground within a small left window:

```text
(tão|tao|mais|menos|muito|bem|quase|bastante)? CURATED_GROUND
```

The selected `ground_text` remains the curated ground, not the intensifier.

### Candidate Filter

Use a native Spark prefilter:

```text
\b(?:tão|tao|mais|menos|muito|bem|quase|bastante)?\s*(CURATED_GROUND)\s+como\s+(?:um|uma|uns|umas)\b
```

### Vehicle Rules

Reuse spec 0006 vehicle extraction, but emit raw and cleaned vehicle fields.
This experiment is about left context recall, not right boundary complexity.

### Expected Upside

This is likely the safest expansion because it preserves the high-precision
article connector.

### Main Risk

It may not add much volume. If most useful examples already have the ground
immediately before `como`, this experiment will be clean but small.

### Promotion Criteria

Promote if one-shard results show:

- at least 20% incremental candidates over spec 0006;
- low review burden;
- meaningful new grounds or pairs, not only duplicates of existing examples.

## Recommended Order

Run in this order:

1. Bare `como` with curated quality grounds only.
2. Broader ground window for `como + article`.
3. `que nem` and `feito`.

Rationale:

- Bare `como` probably has the highest candidate upside.
- Broader ground window is likely the safest quality improvement.
- `que nem` and `feito` are promising, but their noise profile is less clear.

## Notebook Plan

Create one exploratory notebook:

```text
notebooks/02_dataset_expansion_experiments_one_shard.ipynb
```

The notebook should run all three experiments over:

```text
data/raw/brwac-clean-1.txt.gz
data/bronze/brwac_segments
```

Each experiment should be independently runnable and write to a separate
subdirectory under:

```text
outputs/experiments/
```

The notebook should end with a comparison table:

```text
experiment_slug
prefiltered_rows
candidate_rows
distinct_grounds
distinct_vehicle_heads
distinct_pairs
review_keep_rate
top_false_positive_reason
promotion_recommendation
```

## Decision Rule

After the one-shard notebook:

- promote one experiment if it clearly improves dataset size and review quality;
- keep ambiguous experiments as report-only;
- reject experiments whose top outputs are dominated by role/classification
  uses;
- do not run full corpus until the one-shard review table is acceptable.
