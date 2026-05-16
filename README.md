# Portuguese Simile Candidate Explorer

Spark/PySpark MVP for extracting explicit comparison candidates from Brazilian Portuguese web text.

## Runtime

Run the Jupyter Docker Stacks PySpark image from the repo root:

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

## Docs

- [MVP PRD](.scratch/portuguese-similes-mvp/PRD.md)
- [Implementation issues](.scratch/portuguese-similes-mvp/issues)
- [Specs](docs/specs)
- [Context](docs/context)

## Source Data

https://huggingface.co/datasets/nlpufg/brwac
