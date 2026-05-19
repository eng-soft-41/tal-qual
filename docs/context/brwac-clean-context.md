# brWaC Clean Corpus Context

This document records the local corpus facts and noise patterns that matter for
the current Tal Qual workflow.

## Local Dataset

The project uses the Hugging Face dataset copy `nlpufg/brwac`, stored locally
under:

```text
data/raw/
```

The local version is the `brwac-clean` configuration. It contains plain text
examples, not the full annotated release from the original brWaC paper.

Local structure:

```text
data/
  file_names.txt
  raw/
    brwac-clean-1.txt.gz
    ...
    brwac-clean-12.txt.gz
```

Metadata from the local copy:

- Dataset config: `brwac-clean`
- Version: `1.0.0`
- Split: `train`
- Number of examples: `3,530,796`
- Features: `id: int64`, `text: string`
- Compressed data files: 12 `.txt.gz` files
- Local compressed size: about 2.6 GB
- Text size in metadata: about 7.4 GB
- Total size in metadata: about 10.2 GB

## Text Format

The files can be streamed directly as gzip text files. Full decompression is
not required for normal processing.

`<END>` markers should be treated as hard segment boundaries. The bronze layer
splits these markers before candidate extraction so a candidate cannot span
unrelated corpus fragments.

The core bronze fields are:

```text
source_file
original_line_id
segment_id
text_original
text_normalized
match_text
```

## Why Spark Still Matters

The corpus is large enough that Spark remains useful for:

- reading compressed shards;
- splitting text into **Bronze Segments**;
- applying a native regex prefilter;
- running extraction only on plausible rows;
- writing Parquet and compact CSV **Analysis Outputs**.

The current notebook uses a native Spark `rlike` prefilter before the Python
UDF. This is the reason the full-shard workflow is fast enough for iteration.

## Corpus Noise That Matters

Raw `como` is extremely frequent and noisy. Earlier scans showed many matches
for broad connectors, but most are not useful for the first visualization
dataset.

Common noise categories:

- classification or role statements: `trabalha como advogado`,
  `conhecido como X`;
- examples: `como a flauta, a viola`;
- additive uses: `assim como`;
- temporal or habitual uses: `como todos os anos`;
- procedural clauses: `Como se dará...`;
- opinion or appearance: `parece melhor`, `parece provável`;
- participial uses: `feito por`, `filme feito em 1979`;
- literal comparisons that are valid candidates but not necessarily figurative.

These findings justify the current narrow extraction contract.

## Relevance To Current Vehicle Filtering

Even after narrowing to `GROUND como artigo VEHICLE`, the corpus can produce
bad or weak **Vehicle Text**. Future filters should pay attention to:

- generic heads: `coisa`, `forma`, `tipo`, `espécie`, `parte`, `meio`,
  `processo`, `exemplo`, `tema`;
- stopword or pronoun starts: `de`, `em`, `o`, `a`, `ele`, `ela`, `todo`;
- role/classification left context: `usado`, `utilizado`, `conhecido`,
  `tratado`, `considerado`, `definido`, `classificado`, `entendido`;
- URL, symbol, percentage, and numeric noise;
- overlong vehicle tails that should be rejected rather than silently
  truncated;
- discourse continuations that start with plausible words but do not form a
  useful comparison image.

## Current Full-Shard Target

The current canonical full-shard target is:

```text
data/raw/brwac-clean-1.txt.gz
```

The preferred notebook configuration observed locally is:

```text
TAL_QUAL_SPARK_MASTER=local[4]
TAL_QUAL_SPARK_PARALLELISM=4
TAL_QUAL_SPARK_SHUFFLE_PARTITIONS=4
```

This configuration was faster than local 5 or 6 worker variants during recent
full-shard runs.

## Future Use

Use this context when improving:

- **Vehicle Text** rejection rules;
- native Spark prefilters;
- quality review samples;
- **Analysis Outputs** that explain corpus noise and extraction confidence.

Do not use this context to broaden the supported connector set before the
current como-article workflow has stronger vehicle filtering and WebApp-ready
outputs.
