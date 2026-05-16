# MVP SPEC — Portuguese Simile Candidate Explorer

## 1. Project Summary

This MVP adapts the idea behind The Pudding’s simile analysis to Brazilian Portuguese, but with a smaller and more feasible scope for a short Big Data capstone.

The system uses **Apache Spark / PySpark** to scan one full compressed brWaC
shard and extract **candidate explicit comparisons** based on narrow connector
patterns such as:

```text
como um / como uma
como se
tal qual
que nem
igual a / igual ao / igual à / igual aos / igual às
parece um / parece uma
feito um / feito uma
```

The MVP does **not** include NLP filtering, LLM classification, or a frontend
application. It is focused on proving that Spark can process a meaningful corpus
tier, extract useful candidates, and generate inspectable datasets for notebook
analysis. Frontend visualization remains downstream context.

---

## 2. Capstone Fit

This project satisfies the capstone requirement because:

- **Apache Spark** is the main processing tool.
- The problem is typical of Big Data text processing.
- The architecture runs a tiny sample sanity check and a required one-shard brWaC
  validation.
- The project demonstrates **Volume** and **Variety**:
  - Volume: large-scale Portuguese text corpus.
  - Variety: web text from multiple domains and writing styles.
- The output can support a simple web dashboard or notebook-based visual prototype.

---

## 3. MVP Goal

Create a lightweight Spark-based prototype that answers:

1. Can we extract explicit comparison candidates from Portuguese text using connector rules?
2. Which connectors appear most often?
3. Which comparison phrases or “vehicles” appear most often after each connector?
4. Which patterns are promising for future visualization?

The MVP should be presented as:

> A Spark-based exploratory pipeline for extracting and visualizing explicit comparison candidates in Portuguese text.

Not as:

> A perfect detector of similes, metaphors, or figurative language.

---

## 4. Inspiration and Adaptation

The Pudding project works because it narrows the linguistic problem to a regular English pattern:

```text
as [adjective] as [noun / noun phrase]
```

This makes similes measurable through repeated pairings between a **ground** and a **vehicle**.

For Portuguese, the exact English structure does not translate perfectly, so this MVP adapts the idea by focusing on connector-based comparison patterns:

```text
[context before] + [connector] + [comparison phrase after]
```

Example:

```text
Ele correu como um raio.
```

Possible extraction:

```text
text_before: Ele correu
connector: como um
vehicle_raw: raio
candidate_full_text: Ele correu como um raio
```

---

## 5. Out of Scope

The MVP intentionally excludes:

- NLP filtering with spaCy, NLTK, or Spark NLP.
- LLM-based classification.
- Figurative versus literal classification.
- Tenor / ground / vehicle semantic extraction.
- Metaphor detection.
- Human review interface.
- Frontend visualization app implementation.
- Frontend-ready JSON contracts.
- Real-time processing.
- HDFS integration, unless time allows.
- Production-grade web application.

These can be tested in later phases.

---

## 6. Technical Stack

### Runtime

Docker is the expected runtime. Use **Jupyter Docker Stacks** with a PySpark
image:

```text
quay.io/jupyter/pyspark-notebook
```

### Core technologies

```text
Python
PySpark
Spark SQL DataFrames
Jupyter Notebook / JupyterLab
CSV or Parquet outputs
Optional: Pandas + Matplotlib for charts inside notebook
```

### Recommended Docker command

```bash
docker run --rm -it \
  -p 8888:8888 \
  -p 4040:4040 \
  -p 4041:4041 \
  -v "$PWD":/home/jovyan/work \
  quay.io/jupyter/pyspark-notebook
```

Open the Jupyter URL printed in the terminal.

Spark UI should be available at:

```text
http://localhost:4040
```

---

## 7. Suggested Project Structure

```text
tal-qual/
├── data/
│   ├── raw/
│   │   └── brwac-clean-1.txt.gz
│   ├── bronze/
│   │   └── brwac_segments/
│   └── silver/
│       └── comparison_candidates/
├── notebooks/
│   ├── 01_pyspark_smoke_run.ipynb
│   ├── 02_bronze_text_preparation.ipynb
│   ├── 03_one_shard_end_to_end_validation.ipynb
│   └── 03-1_one_shard_materialized_validation.ipynb
├── outputs/
│   ├── candidates.csv
│   ├── connector_family_counts.csv
│   ├── pattern_type_counts.csv
│   ├── top_vehicles_global.csv
│   ├── top_vehicles_by_family.csv
│   ├── top_vehicles_by_pattern.csv
│   └── sample_examples.csv
├── src/tal_qual/
├── README.md
└── docs/
    ├── specs/
    └── context/
```

---

## 8. Dataset Strategy

### MVP dataset

The required MVP corpus tier is one full compressed brWaC shard:

```text
data/raw/brwac-clean-1.txt.gz
```

Start with the tracked tiny local Portuguese text sample only as a sanity check:

Each line can be one sentence, paragraph, or document fragment.

Example:

```text
Ele correu como um raio pela rua.
A menina estava quieta como uma estátua.
Ela falava como se conhecesse todos os segredos.
O menino era teimoso que nem uma mula.
A noite estava fria feito uma pedra.
O barulho parecia uma tempestade.
```

### Later dataset

After validating the MVP, the same pipeline can be tested on multiple brWaC
shards or another Portuguese corpus.

The important architectural point is that the pipeline starts small but is designed to scale.

---

## 9. Data Pipeline

### Overview

```text
Raw text files
  ↓
Spark ingestion
  ↓
Bronze: basic cleanup
  ↓
Silver: connector-based candidate extraction
  ↓
Gold: aggregation datasets
  ↓
Notebook charts / future web dashboard
```

---

## 10. Data Layers

### 10.1 Raw Layer

Original input text.

Path:

```text
data/raw/
```

No transformations.

---

### 10.2 Bronze Layer

Boundary-safe text segments.

Fields:

```text
source_file
original_line_id
segment_id
text_original
text_normalized
match_text
```

Transformations:

- Split literal `<END>` markers before extraction.
- Remove empty segments.
- Trim whitespace.
- Normalize repeated spaces.
- Preserve original text.
- Create lowercase, accent-preserving match text.

Output:

```text
data/bronze/brwac_segments
```

---

### 10.3 Silver Layer

Extracted comparison candidates.

Fields:

```text
source_file
original_line_id
segment_id
candidate_id
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

Notes:

- One row is emitted per connector match, not per input line or segment.
- `connector_family`, `pattern_type`, `comparison_form`, and `matched_text`
  replace the older ambiguous `connector` field.
- `matched_text` is the exact connector phrase from the normalized segment.
- `vehicle_raw` starts immediately after `matched_text`.
- `vehicle_normalized` lowercases, collapses whitespace, and trims surrounding
  punctuation while preserving leading Portuguese articles.
- `text_before` stores up to 80 characters of left context.
- Right context stops at punctuation, `<END>`, or 120 characters.
- `candidate_id` is deterministic from provenance, offsets, pattern type, and
  matched text.
- `char_start` and `char_end` are zero-based offsets in normalized segment text;
  `char_end` is exclusive.

Output:

```text
data/silver/comparison_candidates
outputs/candidates.csv
```

`outputs/candidates.csv` is a deterministic compact sample, not the full silver
dataset.

---

### 10.4 Gold Layer

Compact aggregation datasets for inspection.

Datasets:

```text
connector_family_counts.csv
pattern_type_counts.csv
top_vehicles_global.csv
top_vehicles_by_family.csv
top_vehicles_by_pattern.csv
sample_examples.csv
```

Output:

```text
outputs/
```

Vehicle outputs use `vehicle_normalized` and include occurrence counts. The
vehicle-ranking outputs also include distinct candidate text counts where useful
to expose repeated boilerplate.

---

## 11. Connector Patterns

Use simple regex-based rules. Generic `como` is intentionally excluded.

```text
connector_family  pattern_type              comparison_form  matched forms
como              como_article              nominal          como um / uma / uns / umas
como              como_se                   clausal          como se
que_nem           que_nem_bare              bare             que nem
tal_qual          tal_qual_bare             bare             tal qual
parecer           parecer_article           nominal          parece / parecia / pareceu + um / uma
feito             feito_article             nominal          feito um, feita uma, feitos uns, feitas umas
igual             igual_preposition         prepositional    igual a / ao / à / aos / às
igual             igual_article             nominal          igual um / uma / uns / umas
igualzinho        igualzinho_preposition    prepositional    igualzinho variants + a / ao / à / aos / às
igualzinho        igualzinho_article        nominal          igualzinho variants + um / uma / uns / umas
```

For extraction, use a limited text window after the connector:

```text
up to punctuation: . , ! ? ; :
or up to 120 characters
```

This keeps candidate phrases readable and avoids capturing entire paragraphs.

---

## 12. Notebook Flow

### Step 1 — Start Spark

Open `work/notebooks/03_one_shard_end_to_end_validation.ipynb` in the Dockerized
Jupyter runtime, or execute it with `nbconvert`:

```bash
docker run --rm \
  -v "$PWD":/home/jovyan/work \
  -w /home/jovyan/work \
  quay.io/jupyter/pyspark-notebook \
  jupyter nbconvert --to notebook --execute notebooks/03_one_shard_end_to_end_validation.ipynb \
    --output 03_one_shard_end_to_end_validation.ipynb \
    --output-dir notebooks \
    --ExecutePreprocessor.timeout=-1
```

For constrained Docker runtimes, use
`notebooks/03-1_one_shard_materialized_validation.ipynb`. It writes and rereads
bronze and silver Parquet between stages and uses lower Spark parallelism.

### Step 2 — Prepare bronze

The notebook reads `data/raw/brwac-clean-1.txt.gz`, splits `<END>` boundaries,
normalizes whitespace, derives lowercase match text, and writes:

```text
data/bronze/brwac_segments
```

### Step 3 — Extract silver candidates

The notebook calls the reusable `tal_qual.silver` extraction functions and
writes:

```text
data/silver/comparison_candidates
```

### Step 4 — Generate gold outputs

The notebook writes compact CSV outputs:

```text
outputs/candidates.csv
outputs/connector_family_counts.csv
outputs/pattern_type_counts.csv
outputs/top_vehicles_global.csv
outputs/top_vehicles_by_family.csv
outputs/top_vehicles_by_pattern.csv
outputs/sample_examples.csv
```

### Step 5 — Inspect charts and examples

The notebook displays connector-family counts, pattern-type counts, top vehicle
tables, and examples with connector family, pattern type, candidate text, and
vehicle fields.

---

## 13. Required Notebook Visualizations

The MVP includes notebook-based inspection, not a frontend app.

### 13.1 Connector frequency

Question:

> Which explicit comparison connector families appear most often?

Chart:

```text
Horizontal or vertical bar chart
```

Dataset:

```text
connector_family_counts.csv
```

---

### 13.2 Pattern frequency

Question:

> Which exact extraction rules appear most often?

Chart:

```text
Horizontal or vertical bar chart
```

Dataset:

```text
pattern_type_counts.csv
```

---

### 13.3 Vehicle and candidate examples

Question:

> What right-context phrases and candidate examples did the extractor produce?

Display:

```text
connector_family | pattern_type | candidate_full_text | vehicle_raw | vehicle_normalized
```

This is important because the MVP is candidate extraction, not perfect
classification.

---

## 14. One-Shard Validation Results

The validated one-shard run used:

```text
Input shard: data/raw/brwac-clean-1.txt.gz
Spark version: 4.1.1
Bronze segment rows: 4,673,057
Silver candidate rows: 58,769
```

Connector-family counts:

```text
como          47,885
que_nem        3,912
igual          3,268
parecer        1,651
feito          1,340
tal_qual         608
igualzinho       105
```

Pattern-type counts:

```text
como_article         33,162
como_se              14,723
que_nem_bare          3,912
igual_preposition     3,210
parecer_article       1,651
feito_article         1,340
tal_qual_bare           608
```

Connector-based extraction is feasible on one meaningful brWaC shard for the
MVP. The run produced enough connector and pattern signal for inspection,
including silver Parquet, compact gold CSV aggregations, charts, and candidate
examples.

---

## 15. Acceptance Criteria

The MVP is complete when:

- It runs inside `quay.io/jupyter/pyspark-notebook`.
- A Spark session starts successfully.
- The notebook runs against one full compressed brWaC shard.
- Bronze output is generated at `data/bronze/brwac_segments`.
- Silver candidate output is generated at `data/silver/comparison_candidates`.
- Each candidate includes provenance, deterministic identity, connector-family,
  pattern-type, comparison-form, matched text, context, vehicle, and offset
  fields.
- Compact gold CSV outputs are saved under `outputs/`.
- At least two notebook visualizations are shown from generated aggregation data.
- Candidate examples are displayed for qualitative inspection.
- Limitations from the one-shard run are clearly documented.
- Frontend visualization remains downstream context, not part of MVP completion.

---

## 16. Known Limitations

Observed limitations from the one-shard validation run:

- Extraction is intentionally connector-based and does not classify literal
  versus figurative usage.
- Generic `como` remains excluded, so recall is deliberately lower in exchange
  for less noise.
- `vehicle_raw` is a bounded right-context phrase, not a syntactic noun phrase
  or semantic vehicle.
- Some top normalized vehicles are discourse continuations from clausal
  patterns, such as `sabe`, `vê`, and `não bastasse`.
- Repeated web boilerplate can still influence frequency outputs, although
  sample examples are deduplicated for inspection.
- No grammatical validation, lemmatization, semantic classification, or human
  review is performed in the MVP.
