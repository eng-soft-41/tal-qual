# Tal Qual

Spark/PySpark workflow for building a visualization-ready Portuguese
`ground -> vehicle` comparison dataset from brWaC.

The current core workflow is the **Como-Article Ground/Vehicle MVP**:

```text
Raw / Bronze corpus segments
  -> native Spark prefilter for curated GROUND como article
  -> strict Python extraction for GROUND como um/uma/uns/umas VEHICLE
  -> gold candidate dataset
  -> compact analysis and WebApp-ready CSV outputs
```

The project now optimizes for a small, high-precision dataset that can support
visualizations of repeated Portuguese comparison pairings such as:

```text
forte como um touro
leve como uma pluma
caiu como uma luva
voar como um avião
```

## Presentation Pages

The Big Data class presentation is available as static HTML under `docs/`.
When GitHub Pages is enabled for the `main` branch `/docs` folder, use:

- Project presentation:
  `https://eng-soft-41.github.io/tal-qual/bigdata-presentation-slides.html`
- Technical pipeline support:
  `https://eng-soft-41.github.io/tal-qual/technical-pipeline-slides.html`

## Local Python Workflow

UV is the expected local Python workflow for setup and tests. From the repo
root, run:

```bash
uv sync
uv run python -m unittest discover -s tests
```

The canonical test command uses Python's standard `unittest` runner because the
current test suite does not require pytest-specific features.

## Runtime

Docker Compose is the expected PySpark/Jupyter runtime. From the repo root,
build the project notebook image and start Jupyter:

```bash
docker compose up --build
```

After the first build, use the faster start command:

```bash
docker compose up
```

Open `http://localhost:8888/lab`, then open the notebook for the run you need.
For the frontend dataset, use the full-corpus workflow:

```text
work/notebooks/01_full_como_article_ground_vehicle_mvp.ipynb
```

The compose file binds Jupyter and Spark UI ports to `127.0.0.1`, so the
passwordless local notebook is not exposed on the network. Spark UI is usually
available at `http://localhost:4040` while a job is running.

The Docker image installs project Python dependencies once at build time. The
repository is mounted into the container at `/home/jovyan/work`, and notebooks
package `src/tal_qual` for Spark Python workers so normal source edits are
visible without rebuilding the image. Rebuild only when `pyproject.toml`
dependencies change:

```bash
docker compose build
```

## Source Data

The real brWaC shards belong under `data/raw/`, which is ignored by Git. The
one-shard development target is:

```text
data/raw/brwac-clean-1.txt.gz
```

Source dataset:

https://huggingface.co/datasets/nlpufg/brwac

## Bronze Preparation

The core notebook can load an existing bronze dataset or build it from the
raw shard.

Bronze output:

```text
data/bronze/brwac_segments
```

Bronze rows include:

```text
source_file
original_line_id
segment_id
text_original
text_normalized
match_text
```

`<END>` markers are treated as hard boundaries before candidate extraction, so
candidate windows do not cross unrelated corpus fragments.

## Core Extraction Workflow

The active frontend dataset comes from:

```text
notebooks/01_full_como_article_ground_vehicle_mvp.ipynb
```

That notebook defaults to all local clean shards:

```text
data/raw/brwac-clean-*.txt.gz
data/bronze/brwac_segments_full
```

The smaller 01 notebooks remain useful for development and comparison:

```text
notebooks/01_como_article_ground_vehicle_mvp.ipynb
notebooks/01_hc_como_article_ground_vehicle_mvp.ipynb
```

All 01 workflows use the same module:

```text
src/tal_qual/como_article_ground_vehicle.py
```

The notebook uses a native Spark `rlike` prefilter before the Python
UDF extraction. On the current machine, this made the full-shard run drop from
about 1954 seconds to about 49 seconds.

On a cold run, the notebook builds bronze if missing and then reloads the
freshly written Parquet before extraction. This keeps the expensive raw gzip
lineage out of candidate extraction and makes subsequent actions start from
the splittable columnar bronze layer.

The current sweet-spot Spark configuration is:

```bash
TAL_QUAL_SPARK_MASTER=local[4]
TAL_QUAL_SPARK_PARALLELISM=4
TAL_QUAL_SPARK_SHUFFLE_PARTITIONS=4
```

For ad hoc larger runs, point the one-shard notebook at another raw shard, a
glob, or a separate bronze output:

```bash
TAL_QUAL_RAW_CORPUS_INPUT=data/raw/brwac-clean-[1-6].txt.gz
TAL_QUAL_BRONZE_PATH=data/bronze/brwac_segments_half
docker compose up
```

Spark Adaptive Query Execution is enabled in the notebooks to coalesce shuffle
partitions for the small grouped output tables as corpus size changes.

For a direct half-corpus comparison, use:

```text
notebooks/01_hc_como_article_ground_vehicle_mvp.ipynb
```

That notebook defaults to `data/raw/brwac-clean-[1-6].txt.gz` and
`data/bronze/brwac_segments_half`, then prints the resolved raw input, bronze
path, and source files before extraction.

For the frontend build, use the full-corpus notebook:

```text
notebooks/01_full_como_article_ground_vehicle_mvp.ipynb
```

That notebook defaults to `data/raw/brwac-clean-*.txt.gz` and
`data/bronze/brwac_segments_full`.

## Frontend Dataset Decision

Use the spec-0006 full-corpus outputs from
`notebooks/01_full_como_article_ground_vehicle_mvp.ipynb` for the first
frontend visualization build.

Dataset expansion experiments around bare `como`, `que nem`, `feito`, broader
ground windows, and spaCy candidate filtering were explored and then deferred.
They found promising future directions, but the operational overhead and memory
pressure were too high for the current build phase. The decision record is:

```text
docs/reports/2026-05-17-dataset-expansion-experiment-retrospective.md
```

Archived experiment notebooks live under:

```text
docs/archive/dataset-expansion-experiments/
```

## Extraction Contract

The core extractor only accepts:

```text
QUALITY_WORD como um/uma/uns/umas VEHICLE
SALIENT_VERB como um/uma/uns/umas VEHICLE
```

Out of scope for the current core:

```text
bare como
que nem
feito
igual
parece
como se fosse
```

The ground must be the token immediately before `como` and must come from the
curated quality adjective or salient verb lists in
[spec 0006](docs/specs/0006-como-article-ground-vehicle-mvp.md).

The vehicle starts immediately after the article. Current vehicle extraction:

- keeps 1 to 5 tokens;
- stops at punctuation or segment boundary;
- preserves the surface phrase;
- lowercases a normalized copy;
- uses the first token as the MVP vehicle head;
- rejects generic, stopword, role/classification, numeric, URL, and symbol
  noise.

## Gold Dataset

Primary output:

```text
data/gold/como_article_ground_vehicle_candidates
```

Important fields:

```text
candidate_id
source_file
original_line_id
segment_id
pattern_type
connector
connector_text
matched_text
candidate_full_text
text_before
tenor_text
ground_text
ground_lemma
ground_type
ground_source
vehicle_text
vehicle_lemma
vehicle_head
vehicle_head_lemma
vehicle_phrase_length_tokens
filter_label
reject_reason
confidence
needs_review
char_start
char_end
connector_start
connector_end
vehicle_start
vehicle_end
```

`connector_text` is included between `ground_text` and `vehicle_text` in review
tables to make examples easy to scan.

## Analysis Outputs

The core workflow writes compact CSVs for inspection, analysis, and future
WebApp visualizations:

```text
outputs/como_article_ground_vehicle_counts.csv
outputs/como_article_vehicle_ground_counts.csv
outputs/como_article_ground_counts.csv
outputs/como_article_vehicle_counts.csv
outputs/como_article_examples.csv
outputs/como_article_review_sample.csv
```

These tables support:

- Ground fingerprints: top vehicles for each ground.
- Vehicle fingerprints: top grounds for each vehicle.
- Dominance/cliche analysis: whether one vehicle dominates a ground.
- Review sampling: fast manual inspection of the extraction quality.

## Near-Term Project Direction

Next work should build the frontend on the current full-corpus spec-0006
outputs instead of reviving the broad connector pipeline:

1. Frontend-ready views.
   Build ground pages, vehicle pages, pair rankings, examples, and summary
   metrics from the existing `outputs/como_article_*.csv` tables.

2. Dataset quality surfaces.
   Expose review status and example snippets in the frontend so noisy tails and
   one-off vehicle heads are visible rather than hidden.

3. Focused analysis.
   Add dominance, diversity, ground-family, vehicle-family, and review-quality
   summary tables only when the frontend needs them.

4. Deferred expansion.
   Revisit bare-`como` and spaCy-assisted filtering after the first frontend is
   working and only with memory-safe batching.

## Useful Files

- [Spec 0006](docs/specs/0006-como-article-ground-vehicle-mvp.md)
- [Core extractor](src/tal_qual/como_article_ground_vehicle.py)
- [Full-corpus notebook](notebooks/01_full_como_article_ground_vehicle_mvp.ipynb)
- [One-shard notebook](notebooks/01_como_article_ground_vehicle_mvp.ipynb)
- [Dataset expansion retrospective](docs/reports/2026-05-17-dataset-expansion-experiment-retrospective.md)
