"""Phase A NLP refinement dataset helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping

REFINED_CANDIDATES_NLP_OUTPUT_PATH = Path("data/gold/refined_candidates_nlp")

SAMPLE_DEBUG_TIER = "sample_debug"
ONE_SHARD_REFINED_TIER = "one_shard_refined"

SILVER_TRACEABILITY_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "source_file",
    "original_line_id",
    "segment_id",
    "connector_family",
    "pattern_type",
    "comparison_form",
    "matched_text",
    "text_before",
    "vehicle_raw",
    "vehicle_normalized",
    "candidate_full_text",
    "char_start",
    "char_end",
)

SCOPE_BY_PATTERN_TYPE: dict[str, str] = {
    "como_article": "primary_nominal_article",
    "feito_article": "primary_nominal_article",
    "parecer_article": "primary_nominal_article",
    "igual_article": "primary_nominal_article",
    "igualzinho_article": "primary_nominal_article",
    "que_nem_bare": "primary_nominal_bare",
    "tal_qual_bare": "primary_nominal_bare",
    "como_se": "clausal",
    "igual_preposition": "prepositional",
    "igualzinho_preposition": "prepositional",
}

OUT_OF_SCOPE = "not_in_first_slice_scope"
_WHITESPACE_RE = re.compile(r"\s+")


def nlp_refinement_scope(pattern_type: str) -> str:
    """Map a silver connector pattern to the Phase A refinement scope."""

    return SCOPE_BY_PATTERN_TYPE.get(pattern_type, OUT_OF_SCOPE)


def build_nlp_parse_text(matched_text: str, vehicle_raw: str) -> str:
    """Build the controlled parse window from connector text and raw vehicle."""

    return _compact_text(matched_text, vehicle_raw)


def refine_candidate_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Carry one silver row forward into the minimal refined dataset shape."""

    refined = {field: row[field] for field in SILVER_TRACEABILITY_FIELDS if field in row}
    refined["nlp_refinement_scope"] = nlp_refinement_scope(str(row.get("pattern_type", "")))
    refined["nlp_parse_text"] = build_nlp_parse_text(
        str(row.get("matched_text", "")),
        str(row.get("vehicle_raw", "")),
    )
    return refined


def refine_candidate_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Carry silver candidate rows forward without changing cardinality."""

    return [refine_candidate_row(row) for row in rows]


def sample_debug_rows(rows: Iterable[Mapping[str, Any]], rows_per_pattern: int = 25) -> list[dict[str, Any]]:
    """Return a deterministic pattern-stratified subset of refined rows."""

    if rows_per_pattern < 1:
        raise ValueError("rows_per_pattern must be at least 1")

    pattern_groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        pattern_groups.setdefault(str(row.get("pattern_type", "")), []).append(row)

    sampled: list[Mapping[str, Any]] = []
    for pattern_type in sorted(pattern_groups):
        ordered_rows = sorted(pattern_groups[pattern_type], key=_silver_row_sort_key)
        sampled.extend(ordered_rows[:rows_per_pattern])

    return refine_candidate_rows(sampled)


def prepare_refined_dataframe(silver_df: Any) -> Any:
    """Create a Spark DataFrame for the minimal refined candidate dataset."""

    from pyspark.sql.functions import col, concat_ws, lit, regexp_replace, trim, when

    scope_column = lit(OUT_OF_SCOPE)
    for pattern_type, scope in SCOPE_BY_PATTERN_TYPE.items():
        scope_column = when(col("pattern_type") == pattern_type, scope).otherwise(scope_column)

    parse_text_column = trim(regexp_replace(concat_ws(" ", col("matched_text"), col("vehicle_raw")), r"\s+", " "))

    return (
        silver_df.select(*SILVER_TRACEABILITY_FIELDS)
        .withColumn("nlp_refinement_scope", scope_column)
        .withColumn("nlp_parse_text", parse_text_column)
    )


def prepare_sample_debug_dataframe(silver_df: Any, rows_per_pattern: int = 25) -> Any:
    """Create the deterministic Spark sample-debug refinement DataFrame."""

    from pyspark.sql import Window
    from pyspark.sql.functions import col, row_number

    if rows_per_pattern < 1:
        raise ValueError("rows_per_pattern must be at least 1")

    sample_window = Window.partitionBy("pattern_type").orderBy(
        col("source_file"),
        col("original_line_id"),
        col("segment_id"),
        col("char_start"),
        col("char_end"),
        col("candidate_id"),
    )

    sampled = (
        silver_df.withColumn("sample_debug_rank", row_number().over(sample_window))
        .where(col("sample_debug_rank") <= rows_per_pattern)
        .drop("sample_debug_rank")
    )
    return prepare_refined_dataframe(sampled).orderBy(
        "pattern_type",
        "source_file",
        "original_line_id",
        "segment_id",
        "char_start",
        "candidate_id",
    )


def prepare_refined_dataframe_for_tier(
    silver_df: Any,
    tier: str = ONE_SHARD_REFINED_TIER,
    rows_per_pattern: int = 25,
) -> Any:
    """Prepare a refined DataFrame for a supported Phase A run tier."""

    if tier == SAMPLE_DEBUG_TIER:
        return prepare_sample_debug_dataframe(silver_df, rows_per_pattern)
    if tier == ONE_SHARD_REFINED_TIER:
        return prepare_refined_dataframe(silver_df)
    raise ValueError(f"Unsupported refinement run tier: {tier}")


def write_refined_parquet(
    refined_df: Any,
    output_path: str | Path = REFINED_CANDIDATES_NLP_OUTPUT_PATH,
    mode: str = "overwrite",
) -> None:
    """Write the refined candidate dataset as Parquet."""

    refined_df.write.mode(mode).parquet(str(output_path))


def _compact_text(*parts: str) -> str:
    return _WHITESPACE_RE.sub(" ", " ".join(part.strip() for part in parts if part.strip())).strip()


def _silver_row_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("source_file", "")),
        int(row.get("original_line_id", 0)),
        int(row.get("segment_id", 0)),
        int(row.get("char_start", 0)),
        int(row.get("char_end", 0)),
        str(row.get("candidate_id", "")),
    )
