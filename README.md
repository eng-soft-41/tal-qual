# Portuguese Simile Candidate Explorer

Spark/PySpark MVP for extracting explicit comparison candidates from one full
compressed brWaC shard.

The current MVP is a Dockerized Jupyter workflow, not a packaged CLI or
frontend app. It prepares boundary-safe bronze text segments, extracts one
silver row per high-value connector match, and writes compact gold CSV outputs
for notebook inspection.

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

Docker is the expected PySpark/Jupyter runtime. Run the Jupyter Docker Stacks
PySpark image from the repo root:

```bash
docker run --rm -it \
  -p 8888:8888 \
  -p 4040:4040 \
  -p 4041:4041 \
  -v "$PWD":/home/jovyan/work \
  quay.io/jupyter/pyspark-notebook
```

Open the Jupyter URL printed by the container, then open
`work/notebooks/01_pyspark_smoke_run.ipynb`. Spark UI is usually available at
`http://localhost:4040` while a job is running. Port `4041` is exposed for a
second Spark UI if the first Spark application is still active.

The notebook inserts `work/src` into `sys.path`, so the mounted repository can
be imported without packaging work. If you prefer an editable install inside the
container, run:

```bash
python -m pip install -e /home/jovyan/work
```

For a non-interactive rerun of the one-shard notebook, execute:

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

## Smoke Run

The MVP smoke run verifies the minimal Dockerized path:

1. start the PySpark notebook container with the repository mounted;
2. start a `SparkSession` from the notebook;
3. import the reusable `tal_qual` module from `src/`;
4. load `data/sample/portuguese-similes-smoke.txt` with Spark;
5. display the sample rows in the notebook.

The tracked sample is intentionally tiny. The real brWaC shards belong under
`data/raw/`, which is ignored by Git so a clean checkout can mount a local data
directory without committing corpus files.

The required MVP corpus tier is one full compressed brWaC shard at:

```text
data/raw/brwac-clean-1.txt.gz
```

A sample run is useful for sanity checks, but the MVP validation target is the
full shard.

## Bronze Preparation

Open `work/notebooks/02_bronze_text_preparation.ipynb` in the same Dockerized
Jupyter runtime to prepare boundary-safe bronze text segments from a local brWaC
shard.

The notebook reads gzipped text from `data/raw/brwac-clean-1.txt.gz`, splits literal
`<END>` markers before later extraction work, removes empty segments, preserves
the source segment text, creates whitespace-normalized text plus lowercase
accent-preserving match text, and writes Parquet output to:

```text
data/bronze/brwac_segments
```

Bronze rows include `source_file`, `original_line_id`, `segment_id`,
`text_original`, `text_normalized`, and `match_text`.

`<END>` markers are treated as hard boundaries before candidate extraction, so
candidate windows do not cross unrelated corpus fragments.

## Extraction Contract

The silver extractor uses narrow, high-value connector patterns and deliberately
excludes generic `como`.

Implemented pattern types:

```text
como_article              como um / uma / uns / umas
como_se                   como se
que_nem_bare              que nem
tal_qual_bare             tal qual
parecer_article           parece / parecia / pareceu + um / uma
feito_article             feito um, feita uma, feitos uns, feitas umas
igual_preposition         igual a / ao / à / aos / às
igual_article             igual um / uma / uns / umas
igualzinho_preposition    igualzinho variants + a / ao / à / aos / às
igualzinho_article        igualzinho variants + um / uma / uns / umas
```

Silver schema fields:

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

`matched_text` is the exact connector phrase from the normalized segment.
`vehicle_raw` starts immediately after that phrase and stops at punctuation,
`<END>`, or 120 characters. `text_before` is capped at 80 characters.
`candidate_id` is deterministic from provenance, offsets, pattern type, and the
matched text.

## One-Shard MVP Validation

Open `work/notebooks/03_one_shard_end_to_end_validation.ipynb` in the
Dockerized Jupyter runtime to validate the full MVP pipeline against
`data/raw/brwac-clean-1.txt.gz`.

For comparison in constrained Docker runtimes, open
`work/notebooks/03-1_one_shard_materialized_validation.ipynb`. It runs the same
one-shard validation but writes and rereads bronze and silver Parquet between
stages instead of keeping the large intermediate DataFrames cached. It also
uses a low-parallelism local Spark profile so the materialized bronze read does
not launch too many Python UDF workers for the notebook container.

The notebook writes:

```text
data/bronze/brwac_segments
data/silver/comparison_candidates
outputs/candidates.csv
outputs/connector_family_counts.csv
outputs/pattern_type_counts.csv
outputs/top_vehicles_global.csv
outputs/top_vehicles_by_family.csv
outputs/top_vehicles_by_pattern.csv
outputs/sample_examples.csv
```

The generated `data/silver` and `outputs` directories are ignored by Git because
they are derived from the local brWaC shard.

The validated one-shard run produced `4,673,057` bronze segment rows and
`58,769` silver candidate rows. Connector-family counts were:

```text
como          47,885
que_nem        3,912
igual          3,268
parecer        1,651
feito          1,340
tal_qual         608
igualzinho       105
```

Observed limitations from that run:

- Extraction is connector-based and does not classify literal versus figurative
  usage.
- Generic `como` remains excluded, so recall is deliberately lower in exchange
  for less noise.
- `vehicle_raw` is a bounded right-context phrase, not a syntactic noun phrase
  or semantic vehicle.
- Some frequent normalized vehicles are discourse continuations from clausal
  patterns, such as `sabe`, `vê`, and `não bastasse`.
- Frontend visualization is downstream context only; this MVP validates the
  extraction pipeline and inspectable outputs.

## Phase A NLP Refinement Layer

Phase A is a post-Spark NLP Refinement Layer. It reads the MVP silver candidate
dataset at `data/silver/comparison_candidates`, preserves one row per silver
candidate, and writes additional structural vehicle fields for analysis. It
does not mutate the silver output and does not classify candidates as
figurative or literal.

Phase A uses spaCy Portuguese after Spark has reduced the corpus to candidate
rows. The first refinement slice extracts a Vehicle Phrase and Vehicle Head
where possible, assigns a Structural Quality Bucket, and separates conservative
Clean Common-Noun Vehicles from broader Chartable Vehicles.

Main refined fields:

```text
nlp_refinement_scope
nlp_parse_text
vehicle_phrase_nlp
vehicle_head
vehicle_head_lemma
vehicle_head_pos
vehicle_phrase_length_tokens
vehicle_extraction_confidence
structural_quality_bucket
vehicle_is_clean_common_noun
vehicle_is_chartable_vehicle
vehicle_reject_reason
nlp_model_name
nlp_model_version
```

`nlp_refinement_scope` records whether a row belongs to
`primary_nominal_article`, `primary_nominal_bare`, `clausal`, or
`prepositional` refinement scope. `vehicle_phrase_nlp` is the readable
syntactic phrase used for inspection. `vehicle_head` and `vehicle_head_lemma`
are the preferred aggregation units for refined vehicle charts.
`structural_quality_bucket` describes syntactic usability, not meaning.
`vehicle_is_clean_common_noun` is the conservative noun-only chart flag;
`vehicle_is_chartable_vehicle` is broader and can include selected proper
names while still excluding pronouns, numerals, empty heads, URL or symbol
noise, verbal continuations, and overly long phrases.

Phase A supports two run tiers:

```text
TAL_QUAL_PHASE_A_TIER=sample_debug
TAL_QUAL_PHASE_A_TIER=one_shard_refined
```

`sample_debug` runs a deterministic, pattern-stratified sample for quick
inspection. `one_shard_refined` runs every row in the validated one-shard
silver dataset and is the Phase A acceptance tier.

Open `work/notebooks/04_phase_a_validation.ipynb` in the Dockerized Jupyter
runtime to load or run Phase A outputs. The notebook compares MVP
`vehicle_normalized` rankings with refined `vehicle_head_lemma` rankings,
shows scope and quality-bucket counts, and displays side-by-side raw and
refined examples.

For a non-interactive sample-debug run:

```bash
docker run --rm \
  -e TAL_QUAL_PHASE_A_TIER=sample_debug \
  -e TAL_QUAL_PHASE_A_LOAD_EXISTING_REFINED=0 \
  -v "$PWD":/home/jovyan/work \
  -w /home/jovyan/work \
  quay.io/jupyter/pyspark-notebook \
  bash -lc 'python -m pip install -e /home/jovyan/work && jupyter nbconvert --to notebook --execute notebooks/04_phase_a_validation.ipynb --ExecutePreprocessor.timeout=3600 --output 04_phase_a_validation.executed.ipynb'
```

For the full one-shard tier, use `TAL_QUAL_PHASE_A_TIER=one_shard_refined`.

Phase A writes the durable Refined Candidate Dataset to:

```text
data/gold/refined_candidates_nlp
```

It also writes compact CSV summaries:

```text
outputs/phase_a_scope_counts.csv
outputs/phase_a_quality_bucket_counts.csv
outputs/phase_a_top_clean_common_noun_heads.csv
outputs/phase_a_top_chartable_vehicle_heads.csv
outputs/phase_a_top_vehicle_heads_by_pattern.csv
outputs/phase_a_refinement_examples.csv
```

The full one-shard Phase A validation run used parser model
`core_news_sm 3.8.0`, preserved row cardinality, and produced `58,797` refined
rows from `58,797` silver candidate rows.

Counts by refinement scope:

```text
primary_nominal_article    36,241
clausal                    14,723
primary_nominal_bare        4,520
prepositional               3,313
```

Counts by Structural Quality Bucket:

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

Top clean common-noun heads from the validation run included `forma`,
`espécie`, `pessoa`, `homem`, `alternativa`, `processo`, `sistema`, `meio`,
`opção`, and `empresa`. The run also exposed parser-quality cleanup candidates,
including quote-prefixed phrases, occasional unhelpful noun-chunk heads, and
web-noise phrases that should be tightened in a later cleanup slice.

Ground adjective extraction and LLM classification remain downstream work.

## Docs

- [MVP PRD](.scratch/portuguese-similes-mvp/PRD.md)
- [Phase A spec](docs/specs/0002-mvp-phase-A-nlp-filter.md)
- [Implementation issues](.scratch/portuguese-similes-mvp/issues)
- [Specs](docs/specs)
- [Context](docs/context)

## Source Data

https://huggingface.co/datasets/nlpufg/brwac
