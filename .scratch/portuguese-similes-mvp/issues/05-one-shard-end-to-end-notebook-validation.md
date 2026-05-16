# One-Shard End-to-End Notebook Validation

Status: complete

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Validate the MVP end to end by running the notebook workflow against one full compressed brWaC shard. The completed slice should demonstrate that the Dockerized Spark notebook can process the required corpus tier, produce bronze/silver/gold outputs, show basic visualizations, and record enough observed results and limitations to support the capstone presentation.

## Acceptance criteria

- [x] The notebook runs against one full compressed brWaC shard as the required MVP corpus.
- [x] The run produces the expected bronze, silver, and gold outputs.
- [x] At least two notebook visualizations are shown from generated aggregation data.
- [x] A candidate examples table is shown with connector family, pattern type, candidate text, and vehicle fields.
- [x] Observed connector and pattern counts from the one-shard run are recorded.
- [x] Known limitations are documented from actual output inspection.
- [x] The MVP answers whether connector-based extraction is feasible on a meaningful brWaC subset.

## Blocked by

- .scratch/portuguese-similes-mvp/issues/04-vehicle-normalization-and-gold-aggregations.md

## Validation notes

Notebook: `notebooks/03_one_shard_end_to_end_validation.ipynb`

Executed with:

```bash
docker run --rm \
  -v /Users/ronalson/Code/engsoft/tal-qual:/home/jovyan/work \
  -w /home/jovyan/work \
  quay.io/jupyter/pyspark-notebook \
  jupyter nbconvert --to notebook --execute notebooks/03_one_shard_end_to_end_validation.ipynb \
    --output 03_one_shard_end_to_end_validation.ipynb \
    --output-dir notebooks \
    --ExecutePreprocessor.timeout=-1
```

Observed run results:

- Input shard: `data/raw/brwac-clean-1.txt.gz`
- Spark version: `4.1.1`
- Bronze segment rows: `4,673,057`
- Silver candidate rows: `58,769`
- Connector-family counts:
  - `como`: `47,885`
  - `que_nem`: `3,912`
  - `igual`: `3,268`
  - `parecer`: `1,651`
  - `feito`: `1,340`
  - `tal_qual`: `608`
  - `igualzinho`: `105`
- Pattern-type counts:
  - `como_article`: `33,162`
  - `como_se`: `14,723`
  - `que_nem_bare`: `3,912`
  - `igual_preposition`: `3,210`
  - `parecer_article`: `1,651`
  - `feito_article`: `1,340`
  - `tal_qual_bare`: `608`

Observed limitations:

- Extraction is intentionally connector-based and does not classify literal versus figurative usage.
- Generic `como` remains excluded, so recall is deliberately lower in exchange for less noise.
- `vehicle_raw` is a bounded right-context phrase, not a syntactic noun phrase or semantic vehicle.
- Some top normalized vehicles are discourse continuations from clausal patterns, such as `sabe`, `vê`, and `não bastasse`.

Feasibility answer:

Connector-based extraction is feasible on one meaningful brWaC shard for the MVP. The one-shard run produced enough connector and pattern signal for inspection, including silver Parquet, compact gold CSV aggregations, charts, and candidate examples.
