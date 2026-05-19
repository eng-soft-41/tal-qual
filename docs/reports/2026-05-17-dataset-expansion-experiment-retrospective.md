# Dataset Expansion Experiment Retrospective

Date: 2026-05-17

Decision: return to the original spec-0006 full-corpus dataset from
`notebooks/01_full_como_article_ground_vehicle_mvp.ipynb` for the first
frontend visualization build.

The expansion experiments found useful directions, but the cost and complexity
are too high for the current project phase. The immediate priority is to build
the frontend around the already-materialized high-precision outputs:

```text
data/gold/como_article_ground_vehicle_candidates
outputs/como_article_ground_vehicle_counts.csv
outputs/como_article_vehicle_ground_counts.csv
outputs/como_article_ground_counts.csv
outputs/como_article_vehicle_counts.csv
outputs/como_article_examples.csv
outputs/como_article_review_sample.csv
```

## Baseline

The original full-corpus spec-0006 workflow extracts:

```text
CURATED_GROUND como um/uma/uns/umas VEHICLE
```

Known full-corpus result:

```text
2,136 kept candidates
940 ground -> vehicle pairs
40 grounds
742 vehicle heads
```

The dataset is small, but it is coherent enough for a first visualization
prototype centered on repeated Portuguese comparison pairings.

## Experiments Run

### Bare `como`, first pass

Notebook:

```text
notebooks/02_dataset_expansion_experiments_one_shard.ipynb
```

Pattern:

```text
CURATED_QUALITY_GROUND como VEHICLE
```

One-shard result:

```text
1,184 candidates
701 rule-accepted candidates
59.2% keep-or-trimmed rate
608 accepted distinct pairs
```

Finding:

- It was the first real volume expansion.
- It found good pairs such as `claro -> água`, `escuro -> breu`,
  `duro -> pedra`, and `doce -> mel`.
- However, the accepted rows were dominated by clause fragments and
  function-word heads such as `se`, `é`, `eu`, `sempre`, `também`, `este`.

Outcome:

```text
Promising, but not frontend-ready.
```

### Broader Window For `como + article`

Notebook:

```text
notebooks/02_dataset_expansion_experiments_one_shard.ipynb
```

Intended pattern:

```text
(tão|tao|mais|menos|muito|bem|quase|bastante)? CURATED_GROUND como um/uma/uns/umas VEHICLE
```

One-shard result:

```text
333 prefiltered rows
334 candidates
316 accepted candidates
94.6% keep-or-trimmed rate
```

Finding:

- Quality was high.
- But the prefilter count was the same as spec 0006.
- The experiment did not truly broaden the match space because the curated
  ground was still immediately before `como`.

Outcome:

```text
Rejected as an expansion strategy.
```

### Colloquial `que nem` / `feito`

Notebook:

```text
notebooks/02_dataset_expansion_experiments_one_shard.ipynb
```

Pattern:

```text
CURATED_GROUND que nem VEHICLE
CURATED_GROUND feito/feita/feitos/feitas VEHICLE
```

One-shard result:

```text
307 candidates
171 rule-accepted candidates
55.7% keep-or-trimmed rate
111 accepted distinct pairs
```

Finding:

- Some true comparisons appeared, such as `caiu que nem papel` and
  `duro feito pedra`.
- Most high-frequency rows were not usable comparisons:
  `claro que nem tudo`, `claro que nem sempre`, and participial `feito`
  readings such as `doces feitos de chocolate`.

Outcome:

```text
Rejected for the current build. Split into separate future experiments if
revisited.
```

### Bare `como` v2 Rule Cleanup

Notebook:

```text
notebooks/03_bare_como_expansion_v2.ipynb
```

Changes:

- Stripped definite article heads in cases like `forte como o pai`, using
  `pai` as `vehicle_head_clean`.
- Rejected many clause/function starts such as `se`, `é`, `eu`, `ele`,
  `sempre`, `também`, possessives, temporal adverbs, and prepositions.
- Added `accepted_review_sample.csv`.

One-shard result after cleanup:

```text
1,184 candidates
772 accepted candidates
65.2% accepted rate
702 accepted distinct pairs
```

Finding:

- Surface noise was reduced.
- Top pairs improved:
  `claro -> água`, `escuro -> breu`, `claro -> luz`, `pesado -> chumbo`,
  `doce -> mel`, `duro -> pedra`, `frágil -> vidro`.
- The accepted sample still contained many role/classification readings:
  `fraco como jogador`, `preso como guerrilheiro`,
  `brilhante como jogador de futebol`, `Livre como estratégia de negócio`.

Outcome:

```text
Still not frontend-ready.
```

### Bare `como` With spaCy Candidate-Level Filter

Notebook:

```text
notebooks/03_bare_como_spacy_filter.ipynb
```

Pipeline:

```text
Spark regex prefilter
  -> bare-como candidate extraction
  -> spaCy only on candidate_full_text snippets
  -> role/visual/POS heuristics
```

Finding:

- spaCy was useful after Spark prefiltering, not before it.
- It successfully separated a high-precision `visual_head_whitelist` subset:
  `claro como água`, `escuro como breu`, `doce como mel`,
  `duro como pedra`, `frágil como vidro`, `pesado como chumbo`.
- The broader `spacy_short_nominal_vehicle` bucket was still too noisy:
  proper names, numbers, roles, abstract nouns, locations, and examples.

Useful one-shard high-precision subset:

```text
visual_head_whitelist rows: 73
```

Outcome:

```text
Technically promising, but deferred.
```

### Final Merged Visualization Pipeline Attempt

Notebooks:

```text
notebooks/04_visualization_dataset_one_shard.ipynb
notebooks/04_hc_visualization_dataset.ipynb
notebooks/04_full_visualization_dataset.ipynb
```

Intended final strategy:

```text
frontend dataset =
  spec-0006 candidates
  + bare-como spaCy candidates where nlp_quality_reason = visual_head_whitelist
```

Finding:

- The strategy was defensible from a data-quality perspective.
- In practice, it introduced too much operational overhead for the current
  machine and project phase.
- Spark JVM failures and memory pressure made the workflow unreliable enough
  to block progress on the frontend.

Outcome:

```text
Deferred. Do not use for the current frontend build.
```

## Why We Are Reverting

The expansion work created new candidate pools, but every broader strategy
introduced at least one of these costs:

- higher memory pressure;
- extra Spark passes;
- candidate collection into pandas for spaCy;
- additional review artifacts;
- more complicated quality semantics;
- unclear frontend contract while the UI has not been built yet.

The project needs a working frontend more than it needs a larger dataset right
now. The original full-corpus output is small, but stable, available, and
understood.

## Current Frontend Data Contract

Use the outputs from `notebooks/01_full_como_article_ground_vehicle_mvp.ipynb`.

Primary dataset:

```text
data/gold/como_article_ground_vehicle_candidates
```

Frontend-ready CSVs:

```text
outputs/como_article_ground_vehicle_counts.csv
outputs/como_article_vehicle_ground_counts.csv
outputs/como_article_ground_counts.csv
outputs/como_article_vehicle_counts.csv
outputs/como_article_examples.csv
outputs/como_article_review_sample.csv
```

Recommended first visualizations:

- ranked `ground -> vehicle` pairs;
- ground detail pages for `cair`, `duro`, `leve`, `rápido`, `forte`,
  `voar`, `brilhar`;
- vehicle detail pages for `luva`, `bomba`, `raio`, `pedra`, `pluma`,
  `touro`;
- dominance views showing how much a ground is concentrated in its top vehicle.

## Deferred Follow-Up

After the frontend is working, revisit expansion as a separate backend/data
quality phase.

Most promising future slice:

```text
bare-como spaCy filter
  -> promote only visual_head_whitelist first
  -> keep spacy_short_nominal_vehicle review-only
  -> run on full corpus only after memory-safe batching is implemented
```

Implementation notes for a future pass:

- Do not collect all candidates to pandas at once on full corpus.
- Write candidate Parquet first, then process spaCy in bounded batches.
- Keep `nlp_quality_label`, `nlp_quality_reason`, and raw/clean vehicle fields.
- Treat expansion outputs as an additive dataset version, not a replacement for
  spec 0006.

## Final Decision

For the current project phase:

```text
Build the frontend on spec-0006 full-corpus outputs from the 01_full notebook.
Defer all expansion experiments.
```
