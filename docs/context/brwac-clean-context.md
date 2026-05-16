## Local `brwac-clean` Dataset Context

This project uses the Hugging Face dataset copy `nlpufg/brwac`, stored locally under:

```txt
data/raw/
```

This local version is the **`brwac-clean`** configuration. It contains plain text examples, not the full annotated CoNLL/Moses release described in the original brWaC paper.

### Local Structure

```txt
data/
  file_names.txt
  raw/
    brwac-clean-1.txt.gz
    ...
    brwac-clean-12.txt.gz
```

### Local Metadata

- Dataset config: `brwac-clean`
- Version: `1.0.0`
- Split: `train`
- Number of examples: **3,530,796**
- Features:
  - `id: int64`
  - `text: string`
- Compressed data files: **12 `.txt.gz` files**
- Local compressed size: about **2.6 GB**
- Text size in metadata: about **7.4 GB**
- Total size in metadata: about **10.2 GB**

### Text Format Notes

The files can be streamed directly as gzip text files. Full decompression is not required for normal processing.

The local Hugging Face loader reads the files with `gzip.open(...)` and converts `<END>` markers into newline boundaries:

```python
line.replace("<END>", "\n").rstrip()
```

For this project, `<END>` should be treated as a paragraph or document-boundary marker during normalization.

### Relevance for This Project

This corpus is suitable for a Big Data / Spark SQL project because it is:

- large enough to justify Spark processing;
- stored as multiple compressed files;
- line-oriented and easy to ingest with Spark text readers;
- noisy enough to require filtering and rule refinement;
- rich in explicit comparison markers such as `como`, `feito`, `parece`, `que nem`, `igual a`, and `tal qual`.

### Initial Scan Findings

A first-pass scan over comparison connectors found many matches, but with substantial noise.

On a 500k-line sample:

| Connector | Count | Per 100k lines |
|---|---:|---:|
| `como` | 941,724 | 188,344.8 |
| `parece` | 60,884 | 12,176.8 |
| `feito` | 50,633 | 10,126.6 |
| `que nem` | 7,768 | 1,553.6 |
| `igual a` | 6,625 | 1,325.0 |
| `tal qual` | 1,183 | 236.6 |

Total first-pass matches on 500k lines: **1,068,817**.

### Second-stage Filtering

A narrower second-stage scan kept higher-value comparison patterns such as:

- `como um/uma`
- `como se`
- `tal qual`
- `que nem`
- `igual a/ao/à/aos/às`
- `parece um/uma`
- `feito um/uma`

It excluded common noisy contexts such as:

- `assim como`
- `como por exemplo`
- `como todos/todas/todo/toda`
- `feito por`

On the same 500k-line scale:

| Pattern | Count | Per 100k lines |
|---|---:|---:|
| `como um/uma` | 66,950 | 13,390.0 |
| `como se` | 30,095 | 6,019.0 |
| `que nem` | 7,748 | 1,549.6 |
| `igual a` | 6,614 | 1,322.8 |
| `parece um/uma` | 2,699 | 539.8 |
| `feito um/uma` | 2,548 | 509.6 |
| `tal qual` | 1,181 | 236.2 |

Total second-stage matches on 500k lines: **117,835**.

The second-stage filter kept about **11%** of the raw first-pass matches while preserving a large candidate pool for sampling, annotation, and rule refinement.

### Known Noise Categories

The corpus contains many non-figurative uses of comparison markers. Common noise categories include:

- `classification`: `trabalha como advogado`, `conhecido como X`
- `example`: `como a flauta, a viola`
- `additive`: `assim como`
- `temporal_or_habitual`: `como todos os anos`
- `procedural`: `Como se dará...`
- `opinion_or_appearance`: `parece melhor`, `parece provável`
- `participle`: `feito por`, `filme feito em 1979`
- `literal_comparison`: explicit comparison but not figurative
- `candidate_simile`: likely figurative comparison
