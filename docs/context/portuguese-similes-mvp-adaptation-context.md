# Context — Portuguese Similes MVP Adaptation

## 1. MVP summary

This MVP adapts the idea behind The Pudding’s simile analysis to Portuguese.

The goal is to build a small but functional data pipeline that uses **Apache Spark / PySpark** to scan a Portuguese text corpus and extract candidate explicit comparisons.

Instead of trying to detect every figure of speech, the MVP focuses on comparison connectors that are relatively easy to search at scale.

Initial connector list:

```text
como um / como uma
como se
tal qual
que nem
igual a / igual ao / igual à / igual aos / igual às
parece um / parece uma
feito um / feito uma
```

The MVP should produce a candidate dataset that can later be refined with NLP tools such as spaCy or NLTK and optionally reviewed/classified with an LLM.

## 2. Project goal

Create a lightweight prototype that proves the idea works.

The MVP should answer:

- Can we extract enough Portuguese comparison candidates from the corpus?
- Which connectors are most common?
- Which comparison vehicles appear most often?
- Which candidates look figurative versus literal?
- Which patterns are promising for interactive visualizations?
- Can the pipeline satisfy the class requirement of using Apache Spark?

## 3. Recommended MVP scope

The MVP should not try to solve metaphor detection broadly.

It should focus on **explicit comparison candidates** because they are easier to extract with rules and Spark.

Recommended first scope:

```text
[context before] + [connector] + [comparison phrase after]
```

Example candidates:

```text
rápido como um raio
frio como gelo
forte como uma pedra
quieto feito um gato
parecia uma sombra
igual a um fantasma
```

The output does not need to be perfect. The goal is to create a useful candidate table for analysis and visualization.

## 4. Dataset strategy

The preferred corpus is **brWaC**, because it is large, Portuguese-language, and appropriate for a Big Data-style text-processing pipeline.

For the MVP, use a sample first.

Recommended stages:

1. Start with a small local sample.
2. Validate extraction rules.
3. Run on a larger subset.
4. Save intermediate outputs as Parquet.
5. Produce summary datasets for visualization.

This keeps the project manageable while still demonstrating Spark’s value.

## 5. MVP pipeline overview

```text
Raw corpus
  ↓
Spark ingestion
  ↓
Text cleaning and normalization
  ↓
Connector-based candidate extraction
  ↓
Candidate window generation
  ↓
Basic filtering
  ↓
Optional NLP refinement
  ↓
Optional LLM classification
  ↓
Aggregated datasets
  ↓
Web visualization prototype
```

## 6. Spark responsibilities

Spark should be the main processing layer.

Spark can handle:

- reading large text files
- splitting lines/documents
- normalizing text
- detecting connector patterns
- extracting context windows
- creating candidate rows
- counting connector frequencies
- aggregating frequent vehicles
- saving candidate and aggregate datasets

Recommended Spark outputs:

```text
data/bronze/
  raw or minimally cleaned text

data/silver/
  comparison candidates

data/gold/
  aggregated visualization datasets
```

## 7. Candidate table

A useful candidate table could include:

```text
candidate_id
source_id
line_id
connector
text_before
matched_text
text_after
candidate_full_text
vehicle_raw
vehicle_normalized
language
char_start
char_end
is_reviewed
classification
confidence
```

For the first MVP, many fields can be empty or estimated. The most important fields are:

```text
connector
candidate_full_text
text_before
matched_text
text_after
vehicle_raw
```

## 8. Basic extraction approach

A simple Spark-first strategy:

1. Read each line or paragraph as text.
2. Normalize whitespace.
3. Lowercase text for matching, while preserving the original version.
4. Search for connector patterns with regex.
5. Extract a fixed-size text window around each match.
6. Extract a rough vehicle phrase after the connector.
7. Save one row per candidate.

Example simplified patterns:

```regex
\bcomo\s+(um|uma|o|a|os|as)?\s+[^,.!?;:]{1,80}
\bcomo\s+se\s+[^,.!?;:]{1,120}
\btal\s+qual\s+[^,.!?;:]{1,80}
\bque\s+nem\s+[^,.!?;:]{1,80}
\bigual\s+(a|ao|à|aos|às)\s+[^,.!?;:]{1,80}
\bparece\s+(um|uma|o|a)?\s+[^,.!?;:]{1,80}
\bfeito\s+(um|uma|o|a)?\s+[^,.!?;:]{1,80}
```

These patterns are intentionally imperfect. They are meant to produce candidates, not final classifications.

## 9. NLP refinement ideas

After Spark creates the candidate dataset, a smaller subset can be refined with NLP.

Possible NLP steps:

- tokenize candidate text
- detect nouns after the connector
- lemmatize vehicle nouns
- remove stopwords and punctuation
- identify adjective + connector + noun patterns
- detect whether the phrase is likely nominal, verbal, or clausal
- filter obvious non-simile structures

Possible tools:

- **spaCy** with a Portuguese model
- **NLTK** for tokenization and simpler preprocessing
- **Spark NLP**, if the class/project wants a more Spark-native NLP layer

For the MVP, NLP should be optional. The core requirement is Spark-based extraction.

## 10. LLM-assisted classification ideas

An LLM can be used after extraction to classify a sample or a refined subset of candidates.

Recommended labels:

```text
figurative_simile
literal_comparison
idiom_or_fixed_expression
non_comparison_false_positive
unclear
```

The LLM can also help extract structured fields:

```text
tenor
ground
vehicle
vehicle_normalized
is_figurative
explanation_short
```

Example LLM classification prompt:

```text
You are classifying Portuguese comparison candidates.

Candidate:
"{candidate_full_text}"

Return JSON with:
- label: one of figurative_simile, literal_comparison, idiom_or_fixed_expression, non_comparison_false_positive, unclear
- tenor: the thing being described, if present
- ground: the shared quality, if present
- vehicle: the comparison image
- vehicle_normalized: normalized noun phrase
- confidence: number from 0 to 1
- explanation_short: one sentence
```

For the MVP, LLM usage should be limited to a sample so the project remains simple and explainable.

## 11. Visualization dataset ideas

The pipeline should generate small JSON or CSV files that can power a web interface.

Suggested outputs:

### 11.1 Connector frequency

Shows which comparison connectors appear most often.

Dataset:

```text
connector,count
como um,1234
como uma,980
que nem,420
tal qual,120
```

Visualization:

- horizontal bar chart
- stacked chart by source or text type
- simple ranking list

### 11.2 Most common vehicles

Shows the most frequent comparison images.

Dataset:

```text
vehicle_normalized,count,top_connectors
pedra,240,"como uma; feito uma"
raio,190,"como um"
gato,155,"feito um; que nem"
```

Visualization:

- ranked list
- bar chart
- word cloud only if used carefully

### 11.3 Connector → vehicle network

Shows relationships between connector types and vehicles.

Example:

```text
como um → raio
como uma → pedra
feito um → gato
que nem → criança
```

Visualization:

- bipartite network
- Sankey diagram
- matrix heatmap

### 11.4 Candidate explorer

A searchable interface for reviewing extracted examples.

Useful filters:

- connector
- vehicle
- label
- confidence
- source
- reviewed/unreviewed

This is probably the most useful MVP interface because it makes the extraction quality visible.

### 11.5 Figurative versus literal breakdown

If LLM or human review is added, show how many candidates are figurative, literal, idiomatic, or false positives.

Visualization:

- stacked bar chart by connector
- donut chart for overall distribution
- review queue with examples

### 11.6 “Portuguese fingerprints”

Inspired by The Pudding’s adjective fingerprints, but adapted to available Portuguese patterns.

Possible versions:

```text
connector fingerprint:
como um/uma → top vehicles

vehicle fingerprint:
pedra → connectors and nearby qualities

adjective/quality fingerprint:
frio → gelo, morte, pedra, noite...
```

The adjective/quality version is more complex because Portuguese patterns may not always expose a clean adjective like English “as dry as.”

For the MVP, connector and vehicle fingerprints are easier.

## 12. Web interface idea

A minimal web interface could include:

1. **Project intro**
   - Explain similes and explicit comparisons.
   - Show examples in Portuguese.

2. **Corpus overview**
   - Number of lines/documents processed.
   - Number of candidates extracted.
   - Most common connectors.

3. **Connector explorer**
   - Bar chart of connectors.
   - Click a connector to see examples.

4. **Vehicle explorer**
   - Ranking of common vehicles.
   - Click a vehicle to see all candidate phrases.

5. **Review panel**
   - Display candidates.
   - Allow manual label correction if feasible.

6. **Methods page**
   - Explain Spark pipeline.
   - Explain limitations.
   - Explain optional NLP/LLM refinement.

## 13. Suggested MVP architecture

```text
notebooks/
  01_ingest_sample.ipynb
  02_extract_candidates_spark.ipynb
  03_aggregate_for_visualization.ipynb
  04_optional_nlp_or_llm_review.ipynb

data/
  raw/
  bronze/
  silver/
  gold/

app/
  simple web prototype
```

The project can run in Jupyter Docker Stacks with PySpark available, or in a local Docker setup that includes Spark and Jupyter.

## 14. Success criteria

The MVP is successful if it can:

- run a Spark job over a Portuguese corpus sample
- extract comparison candidates using connector rules
- save candidates in a structured format
- generate aggregate datasets
- support at least two visualizations
- show example candidates in a simple web interface or notebook
- explain limitations clearly

## 15. Known limitations

The MVP will produce false positives.

Common issues:

- literal comparisons
- incomplete candidate windows
- connector uses that are not similes
- ambiguous noun phrases
- idioms that require cultural interpretation
- multi-word vehicles that are hard to normalize
- missing tenor or ground information

These limitations are acceptable for the MVP as long as the project presents the pipeline as candidate extraction, not perfect simile detection.

## 16. Recommended framing

The project should be framed as:

> A Spark-based exploratory pipeline for extracting and visualizing explicit comparison candidates in Portuguese text.

Avoid claiming:

> A perfect detector of all similes and metaphors in Portuguese.

This keeps the scope realistic and makes the project easier to defend.
