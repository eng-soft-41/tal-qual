# Portuguese Simile Candidate Explorer

Spark/PySpark MVP for extracting explicit comparison candidates from Brazilian Portuguese web text.

## Runtime

Run the Jupyter PySpark Docker image from the repo root:

```bash
docker run --rm -it \
  -p 8888:8888 \
  -p 4040:4040 \
  -p 4041:4041 \
  -v "$PWD":/home/jovyan/work \
  quay.io/jupyter/pyspark-notebook
```

Open the Jupyter URL printed by the container. Spark UI is usually available at `http://localhost:4040` while a job is running.

## Docs

- [MVP PRD](.scratch/portuguese-similes-mvp/PRD.md)
- [Implementation issues](.scratch/portuguese-similes-mvp/issues)
- [Specs](docs/specs)
- [Context](docs/context)

## Source Data

https://huggingface.co/datasets/nlpufg/brwac
