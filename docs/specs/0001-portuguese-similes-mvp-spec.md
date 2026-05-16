# MVP SPEC — Portuguese Simile Candidate Explorer

## 1. Project Summary

This MVP adapts the idea behind The Pudding’s simile analysis to Brazilian Portuguese, but with a smaller and more feasible scope for a short Big Data capstone.

The system uses **Apache Spark / PySpark** to scan a Portuguese text corpus and extract **candidate explicit comparisons** based on connector patterns such as:

```text
como um / como uma
como se
tal qual
que nem
igual a / igual ao / igual à / igual aos / igual às
parece um / parece uma
feito um / feito uma
```

The MVP does **not** include NLP filtering or LLM classification. It is focused on proving that Spark can process the corpus, extract useful candidates, and generate datasets for visual exploration.

---

## 2. Capstone Fit

This project satisfies the capstone requirement because:

- **Apache Spark** is the main processing tool.
- The problem is typical of Big Data text processing.
- The architecture can scale from a small sample to a larger corpus.
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
- Real-time processing.
- HDFS integration, unless time allows.
- Production-grade web application.

These can be tested in later phases.

---

## 6. Technical Stack

### Runtime

Use **Jupyter Docker Stacks** with a PySpark image:

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
portuguese-simile-explorer/
├── data/
│   ├── raw/
│   │   └── brwac-clean-1.txt
│   │       ...
│   ├── bronze/
│   ├── silver/
│   └── gold/
│   └── 01_mvp_candidate_extraction.ipynb
├── outputs/
│   ├── candidates.csv
│   ├── connector_counts.csv
│   ├── top_vehicle_raw.csv
│   └── sample_examples.csv
├── README.md
├── docs/
│   ├── specs/
│   └── context/
└── README.md
```

---

## 8. Dataset Strategy

### MVP dataset

Dataset is located at `data/raw`. See `data/raw-file-names.txt` for a list of all files names.

Start with a small local Portuguese text sample:

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

After validating the MVP, the same pipeline can be tested on a larger subset from brWaC or another Portuguese corpus.

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

Minimally cleaned text.

Fields:

```text
document_id
line_id
text_original
text_normalized
```

Transformations:

- Remove empty lines.
- Trim whitespace.
- Normalize repeated spaces.
- Preserve original text.
- Create lowercase version only for matching.

Output:

```text
data/bronze/text_clean.parquet
```

---

### 10.3 Silver Layer

Extracted comparison candidates.

Fields:

```text
candidate_id
document_id
line_id
connector
pattern_type
text_before
matched_text
text_after
candidate_full_text
vehicle_raw
char_start
char_end
```

Notes:

- `vehicle_raw` is a rough phrase after the connector.
- No NLP normalization is performed in the MVP.
- No figurative/literal label is produced in the MVP.

Output:

```text
data/silver/comparison_candidates.parquet
outputs/candidates.csv
```

---

### 10.4 Gold Layer

Visualization-ready aggregation datasets.

Datasets:

```text
connector_counts.csv
pattern_type_counts.csv
top_vehicle_raw.csv
sample_examples.csv
```

Output:

```text
data/gold/
outputs/
```

---

## 11. Connector Patterns

Use simple regex-based rules.

```python
CONNECTOR_PATTERNS = {
    "como_um_uma": r"\\bcomo\\s+(um|uma)\\b",
    "como_se": r"\\bcomo\\s+se\\b",
    "tal_qual": r"\\btal\\s+qual\\b",
    "que_nem": r"\\bque\\s+nem\\b",
    "igual_a": r"\\bigual\\s+(a|ao|à|aos|às)\\b",
    "parece_um_uma": r"\\bparece\\s+(um|uma)\\b",
    "feito_um_uma": r"\\bfeito\\s+(um|uma)\\b",
}
```

For extraction, use a limited text window after the connector:

```text
up to punctuation: . , ! ? ; :
or up to 80–120 characters
```

This keeps candidate phrases readable and avoids capturing entire paragraphs.

---

## 12. Notebook Flow

### Step 1 — Start Spark

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("Portuguese Simile Candidate Explorer MVP")
    .master("local[*]")
    .getOrCreate()
)

spark
```

---

### Step 2 — Load raw text

```python
from pyspark.sql import functions as F

raw_df = (
    spark.read
    .text("../data/raw/sample_pt.txt")
    .withColumnRenamed("value", "text_original")
)
```

---

### Step 3 — Create bronze dataset

```python
bronze_df = (
    raw_df
    .withColumn("line_id", F.monotonically_increasing_id())
    .withColumn("text_original", F.trim(F.col("text_original")))
    .filter(F.col("text_original") != "")
    .withColumn("text_normalized", F.regexp_replace(F.col("text_original"), r"\\s+", " "))
    .withColumn("text_match", F.lower(F.col("text_normalized")))
)
```

---

### Step 4 — Extract candidates

For each pattern:

1. Match connector.
2. Extract connector text.
3. Extract text before connector.
4. Extract text after connector.
5. Extract rough `vehicle_raw` from the beginning of the text after connector.

Expected output example:

```text
sentence: Ele correu como um raio pela rua.
connector: como um
pattern_type: como_um_uma
text_before: Ele correu
text_after: raio pela rua.
vehicle_raw: raio pela rua
```

---

### Step 5 — Generate aggregations

Required aggregations:

```text
connector frequency
pattern type frequency
top raw vehicles / right-context phrases
sample examples by connector
```

---

### Step 6 — Export outputs

Write both analysis-friendly and visualization-friendly files:

```python
silver_df.write.mode("overwrite").parquet("../data/silver/comparison_candidates.parquet")
connector_counts_df.write.mode("overwrite").option("header", True).csv("../outputs/connector_counts.csv")
top_vehicle_df.write.mode("overwrite").option("header", True).csv("../outputs/top_vehicle_raw.csv")
examples_df.write.mode("overwrite").option("header", True).csv("../outputs/sample_examples.csv")
```

---

## 13. Required Visualizations

The MVP should include at least two notebook visualizations.

### 13.1 Connector frequency

Question:

> Which explicit comparison connectors appear most often?

Chart:

```text
Horizontal or vertical bar chart
```

Dataset:

```text
connector_counts.csv
```

---

### 13.2 Top raw vehicles / right-context phrases

Question:

> What comparison phrases appear most often after the connectors?

Chart:

```text
Bar chart or ranked list
```

Dataset:

```text
top_vehicle_raw.csv
```

---

### 13.3 Candidate examples table

Question:

> What do the extracted candidates look like?

Display:

```text
connector | candidate_full_text | vehicle_raw
```

This is important because the MVP is candidate extraction, not perfect classification.

---

## 14. Acceptance Criteria

The MVP is complete when:

- It runs inside `quay.io/jupyter/pyspark-notebook`.
- A Spark session starts successfully.
- A local Portuguese text sample is loaded with Spark.
- At least 5 connector pattern types are implemented.
- A silver candidate dataset is generated.
- Each candidate includes:
  - connector
  - pattern type
  - text before
  - matched text
  - text after
  - candidate full text
  - raw vehicle phrase
- At least 2 gold aggregation datasets are generated.
- At least 2 notebook visualizations are shown.
- Output files are saved under `outputs/`.
- Limitations are clearly documented.

---

## 15. Known Limitations

The MVP will produce noisy candidates.

Expected issues:

- Literal comparisons.
- False positives.
- Incomplete candidate windows.
- Long or messy right-context phrases.
- Repeated web text fragments.
- Connector uses that are not figurative.
- No grammatical validation.
- No semantic classification.

These are acceptable because the MVP is designed to test extraction feasibility, not linguistic accuracy.
