# Backend-Ready Comparison Dataset

## Goal

Produce a stable, backend-ingestable dataset from the full-corpus
`como_article_ground_vehicle` extraction.

The backend should not read Spark output directories directly. This project
owns the extraction, cleanup, aggregation, and export contract. The backend
owns persistence and API access.

## Source Of Truth

Input artifacts:

```text
data/gold/como_article_ground_vehicle_candidates
outputs/como_article_ground_vehicle_counts.csv
outputs/como_article_vehicle_ground_counts.csv
outputs/como_article_ground_counts.csv
outputs/como_article_vehicle_counts.csv
outputs/como_article_examples.csv
outputs/como_article_review_sample.csv
```

The canonical generation notebook remains:

```text
notebooks/01_full_como_article_ground_vehicle_mvp.ipynb
```

## Decision

Add a backend export layer under:

```text
data/export/backend/comparisons/v1/
```

This directory should contain normal single-file JSONL and CSV assets, not
Spark `part-*` directories.

## Export Files

Required files:

```text
data/export/backend/comparisons/v1/candidates.jsonl
data/export/backend/comparisons/v1/ground_vehicle_counts.json
data/export/backend/comparisons/v1/vehicle_ground_counts.json
data/export/backend/comparisons/v1/ground_counts.json
data/export/backend/comparisons/v1/vehicle_counts.json
data/export/backend/comparisons/v1/examples.jsonl
data/export/backend/comparisons/v1/manifest.json
```

Optional debug files:

```text
data/export/backend/comparisons/v1/review_sample.jsonl
data/export/backend/comparisons/v1/rejected_or_review_candidates.jsonl
```

## Candidate Record Contract

Each line in `candidates.jsonl` is one comparison candidate.

Required fields:

```json
{
  "candidate_id": "string",
  "dataset_version": "v1",
  "pattern_type": "como_article_ground_vehicle",
  "connector_text": "como um",
  "candidate_full_text": "Sentia-se forte como um touro",
  "text_before": "Sentia-se",
  "tenor_text": "Sentia-se",
  "tenor_lemma": "sentia-se",
  "tenor_confidence": "fallback_left_context",
  "ground_text": "forte",
  "ground_lemma": "forte",
  "ground_type": "quality_adjective",
  "ground_source": "curated_quality_list",
  "vehicle_text_raw": "touro",
  "vehicle_text_clean": "touro",
  "vehicle_tail_text": "",
  "vehicle_cleaning_rule": "unchanged",
  "vehicle_lemma": "touro",
  "vehicle_head": "touro",
  "vehicle_head_lemma": "touro",
  "vehicle_head_clean": "touro",
  "vehicle_head_clean_lemma": "touro",
  "vehicle_phrase_length_tokens": 1,
  "quality_label": "keep",
  "quality_reason": [],
  "visualization_ready": true,
  "confidence": 0.95,
  "needs_review": false,
  "source_file": "brwac-clean-1.txt.gz",
  "original_line_id": 123,
  "segment_id": 0,
  "char_start": 10,
  "char_end": 31,
  "connector_start": 16,
  "connector_end": 23,
  "vehicle_start": 24,
  "vehicle_end": 29
}
```

Compatibility notes:

- `vehicle_text_raw` should preserve the current extracted phrase.
- `vehicle_text_clean` should be the backend/frontend display default.
- `vehicle_head_clean_lemma` should be the aggregation key used by the
  exported count files.
- Existing fields may be copied from the current gold Parquet where no cleanup
  is available yet.

## Quality Pass

Add a deterministic candidate-level cleanup pass before backend export.

Minimum v1 cleanup rules:

- If vehicle raw text is one token, mark `vehicle_cleaning_rule = "unchanged"`.
- Trim obvious adjunct tails after common comparison heads:
  `luva`, `bomba`, `raio`, `pedra`, `rocha`, `pluma`, `touro`, `flecha`,
  `borboleta`, `pássaro`, `avião`.
- Trim after likely clause starts such as `é`, `foi`, `era`, `fica`, `tem`,
  `deve`, `ele`, `ela`, `isso`.
- Mark role/classification-like examples as `quality_label = "review"` unless
  the existing extractor already rejected them.
- Set `visualization_ready = quality_label in ("keep", "trimmed")`.

Do not delete borderline candidates in v1. Keep them with quality metadata so
the backend can expose both raw and visualization-ready views.

## Count Contracts

`ground_vehicle_counts.json` should be grouped by:

```text
ground_lemma
vehicle_head_clean_lemma
```

Record shape:

```json
{
  "ground_lemma": "forte",
  "vehicle_head_clean_lemma": "touro",
  "count": 17,
  "example_candidate_ids": ["..."]
}
```

`vehicle_ground_counts.json` should be the reverse grouping:

```json
{
  "vehicle_head_clean_lemma": "touro",
  "ground_lemma": "forte",
  "count": 17,
  "example_candidate_ids": ["..."]
}
```

`ground_counts.json`:

```json
{
  "ground_lemma": "forte",
  "count": 97,
  "distinct_vehicle_count": 31,
  "top_vehicle_head_clean_lemma": "touro",
  "top_vehicle_count": 17,
  "top_vehicle_share": 0.1753
}
```

`vehicle_counts.json`:

```json
{
  "vehicle_head_clean_lemma": "luva",
  "count": 533,
  "distinct_ground_count": 6,
  "top_ground_lemma": "cair",
  "top_ground_count": 452,
  "top_ground_share": 0.8480
}
```

## Manifest Contract

`manifest.json` should include:

```json
{
  "dataset_name": "tal-qual-comparisons",
  "dataset_version": "v1",
  "pattern_type": "como_article_ground_vehicle",
  "generated_at": "ISO-8601 timestamp",
  "source_gold_path": "data/gold/como_article_ground_vehicle_candidates",
  "candidate_count": 2136,
  "visualization_ready_count": 0,
  "ground_count": 40,
  "vehicle_count": 742,
  "ground_vehicle_pair_count": 940,
  "schema_version": 1
}
```

## Implementation Tasks

1. Add export constants to `src/tal_qual/como_article_ground_vehicle.py`.
2. Add a pure-Python cleanup function for a candidate row.
3. Add Spark DataFrame transformation that appends cleanup fields.
4. Add export writer functions for JSONL and JSON aggregate files.
5. Add unit tests for cleanup rules and export schema.
6. Add or update a notebook/script cell that writes
   `data/export/backend/comparisons/v1/`.
7. Validate generated row counts against the current full-corpus review.

## Acceptance Criteria

- `uv run python -m unittest discover -s tests` passes.
- Running the full-corpus workflow creates all required export files.
- `manifest.json` count fields match the exported files.
- Aggregates use `vehicle_head_clean_lemma`, not contaminated raw vehicle
  phrases.
- Backend can seed Mongo from the export directory without Spark or PySpark.
