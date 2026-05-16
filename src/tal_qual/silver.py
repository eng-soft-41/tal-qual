"""Silver candidate extraction for narrow Portuguese comparison connectors."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SILVER_OUTPUT_PATH = Path("data/silver/comparison_candidates")
CANDIDATE_SAMPLE_OUTPUT_PATH = Path("outputs/candidates.csv")
CONNECTOR_FAMILY_COUNTS_OUTPUT_PATH = Path("outputs/connector_family_counts.csv")
PATTERN_TYPE_COUNTS_OUTPUT_PATH = Path("outputs/pattern_type_counts.csv")
TOP_VEHICLES_GLOBAL_OUTPUT_PATH = Path("outputs/top_vehicles_global.csv")
TOP_VEHICLES_BY_FAMILY_OUTPUT_PATH = Path("outputs/top_vehicles_by_family.csv")
TOP_VEHICLES_BY_PATTERN_OUTPUT_PATH = Path("outputs/top_vehicles_by_pattern.csv")
SAMPLE_EXAMPLES_OUTPUT_PATH = Path("outputs/sample_examples.csv")

LEFT_CONTEXT_CHARS = 80
RIGHT_CONTEXT_CHARS = 120

_VEHICLE_BOUNDARY_RE = re.compile(r"<END>|[,.!?;:]")
_SURROUNDING_PUNCTUATION_RE = re.compile(r"^[\s,.;:!?]+|[\s,.;:!?]+$")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ConnectorPattern:
    connector_family: str
    pattern_type: str
    comparison_form: str
    regex: re.Pattern[str]


CONNECTOR_PATTERNS: tuple[ConnectorPattern, ...] = (
    ConnectorPattern("como", "como_article", "nominal", re.compile(r"\bcomo\s+(?:um|uma|uns|umas)\b")),
    ConnectorPattern("como", "como_se", "clausal", re.compile(r"\bcomo\s+se\b")),
    ConnectorPattern("que_nem", "que_nem_bare", "bare", re.compile(r"\bque\s+nem\b")),
    ConnectorPattern("tal_qual", "tal_qual_bare", "bare", re.compile(r"\btal\s+qual\b")),
    ConnectorPattern("parecer", "parecer_article", "nominal", re.compile(r"\bparec(?:e|ia|eu)\s+um(?:a)?\b")),
    ConnectorPattern(
        "feito",
        "feito_article",
        "nominal",
        re.compile(r"\b(?:feito\s+um|feita\s+uma|feitos\s+uns|feitas\s+umas)\b"),
    ),
    ConnectorPattern(
        "igualzinho",
        "igualzinho_preposition",
        "prepositional",
        re.compile(r"\bigualzinh(?:o|a|os|as)\s+(?:a|ao|à|aos|às)\b"),
    ),
    ConnectorPattern(
        "igualzinho",
        "igualzinho_article",
        "nominal",
        re.compile(r"\bigualzinh(?:o|a|os|as)\s+(?:um|uma|uns|umas)\b"),
    ),
    ConnectorPattern(
        "igual",
        "igual_preposition",
        "prepositional",
        re.compile(r"\bigual\s+(?:a|ao|à|aos|às)\b"),
    ),
    ConnectorPattern("igual", "igual_article", "nominal", re.compile(r"\bigual\s+(?:um|uma|uns|umas)\b")),
)


def normalize_vehicle(vehicle_raw: str) -> str:
    """Normalize vehicle text while preserving leading Portuguese articles."""

    trimmed = _SURROUNDING_PUNCTUATION_RE.sub("", vehicle_raw.lower())
    return _WHITESPACE_RE.sub(" ", trimmed).strip()


def extract_candidate_rows(
    source_file: str,
    original_line_id: int,
    segment_id: int,
    text_normalized: str,
    match_text: str | None = None,
) -> list[dict[str, object]]:
    """Extract one silver candidate row per narrow connector match."""

    text_match = (match_text if match_text is not None else text_normalized).lower()
    rows: list[dict[str, object]] = []

    for pattern in CONNECTOR_PATTERNS:
        for match in pattern.regex.finditer(text_match):
            char_start, char_end = match.span()
            matched_text = text_normalized[char_start:char_end]
            text_before = text_normalized[:char_start].rstrip()[-LEFT_CONTEXT_CHARS:].lstrip()
            vehicle_raw = _extract_right_context(text_normalized, char_end)
            candidate_full_text = _compact_context(text_before, matched_text, vehicle_raw)

            rows.append(
                {
                    "source_file": source_file,
                    "original_line_id": original_line_id,
                    "segment_id": segment_id,
                    "candidate_id": _candidate_id(
                        source_file=source_file,
                        original_line_id=original_line_id,
                        segment_id=segment_id,
                        char_start=char_start,
                        char_end=char_end,
                        pattern_type=pattern.pattern_type,
                        matched_text=matched_text,
                    ),
                    "connector_family": pattern.connector_family,
                    "pattern_type": pattern.pattern_type,
                    "comparison_form": pattern.comparison_form,
                    "matched_text": matched_text,
                    "text_before": text_before,
                    "vehicle_raw": vehicle_raw,
                    "vehicle_normalized": normalize_vehicle(vehicle_raw),
                    "candidate_full_text": candidate_full_text,
                    "char_start": char_start,
                    "char_end": char_end,
                }
            )

    return sorted(rows, key=lambda row: (row["char_start"], row["char_end"], row["pattern_type"]))


def prepare_silver_dataframe(bronze_df: Any) -> Any:
    """Create a Spark silver DataFrame from prepared bronze segment rows."""

    from pyspark.sql.functions import col, explode, udf
    from pyspark.sql.types import ArrayType, IntegerType, LongType, StringType, StructField, StructType

    candidate_schema = ArrayType(
        StructType(
            [
                StructField("source_file", StringType(), nullable=False),
                StructField("original_line_id", LongType(), nullable=False),
                StructField("segment_id", IntegerType(), nullable=False),
                StructField("candidate_id", StringType(), nullable=False),
                StructField("connector_family", StringType(), nullable=False),
                StructField("pattern_type", StringType(), nullable=False),
                StructField("comparison_form", StringType(), nullable=False),
                StructField("matched_text", StringType(), nullable=False),
                StructField("text_before", StringType(), nullable=False),
                StructField("vehicle_raw", StringType(), nullable=False),
                StructField("vehicle_normalized", StringType(), nullable=False),
                StructField("candidate_full_text", StringType(), nullable=False),
                StructField("char_start", IntegerType(), nullable=False),
                StructField("char_end", IntegerType(), nullable=False),
            ]
        )
    )

    extract_candidates = udf(extract_candidate_rows, candidate_schema)

    return (
        bronze_df.withColumn(
            "candidate",
            explode(
                extract_candidates(
                    col("source_file"),
                    col("original_line_id"),
                    col("segment_id"),
                    col("text_normalized"),
                    col("match_text"),
                )
            ),
        )
        .select("candidate.*")
    )


def write_silver_parquet(
    silver_df: Any,
    output_path: str | Path = SILVER_OUTPUT_PATH,
    mode: str = "overwrite",
) -> None:
    """Write the full silver candidate dataset as Spark Parquet."""

    silver_df.write.mode(mode).parquet(str(output_path))


def candidate_sample_dataframe(silver_df: Any, sample_size: int = 5000) -> Any:
    """Build the deterministic compact candidate sample for CSV output."""

    from pyspark.sql.functions import col

    return (
        silver_df.orderBy(
            col("source_file"),
            col("original_line_id"),
            col("segment_id"),
            col("char_start"),
            col("pattern_type"),
        )
        .limit(sample_size)
    )


def connector_family_counts_dataframe(silver_df: Any) -> Any:
    """Count candidates by connector family."""

    from pyspark.sql.functions import col

    return silver_df.groupBy("connector_family").count().orderBy(col("count").desc(), col("connector_family"))


def pattern_type_counts_dataframe(silver_df: Any) -> Any:
    """Count candidates by exact pattern type."""

    from pyspark.sql.functions import col

    return silver_df.groupBy("pattern_type").count().orderBy(col("count").desc(), col("pattern_type"))


def top_vehicles_global_dataframe(silver_df: Any) -> Any:
    """Count normalized vehicles globally."""

    return _top_vehicles_dataframe(silver_df, [])


def top_vehicles_by_family_dataframe(silver_df: Any) -> Any:
    """Count normalized vehicles by connector family."""

    return _top_vehicles_dataframe(silver_df, ["connector_family"])


def top_vehicles_by_pattern_dataframe(silver_df: Any) -> Any:
    """Count normalized vehicles by pattern type."""

    return _top_vehicles_dataframe(silver_df, ["pattern_type"])


def sample_examples_dataframe(silver_df: Any, examples_per_pattern: int = 20) -> Any:
    """Build deterministic deduplicated examples per pattern type."""

    from pyspark.sql import Window
    from pyspark.sql.functions import col, row_number

    dedupe_window = Window.partitionBy("pattern_type", "candidate_full_text").orderBy(
        col("source_file"),
        col("original_line_id"),
        col("segment_id"),
        col("char_start"),
        col("candidate_id"),
    )
    deduped = (
        silver_df.withColumn("dedupe_rank", row_number().over(dedupe_window))
        .where(col("dedupe_rank") == 1)
        .drop("dedupe_rank")
    )
    example_window = Window.partitionBy("pattern_type").orderBy(
        col("source_file"),
        col("original_line_id"),
        col("segment_id"),
        col("char_start"),
        col("candidate_id"),
    )

    return (
        deduped.withColumn("example_rank", row_number().over(example_window))
        .where(col("example_rank") <= examples_per_pattern)
        .orderBy("pattern_type", "example_rank")
    )


def write_gold_csv_outputs(
    silver_df: Any,
    candidate_sample_path: str | Path = CANDIDATE_SAMPLE_OUTPUT_PATH,
    connector_family_counts_path: str | Path = CONNECTOR_FAMILY_COUNTS_OUTPUT_PATH,
    pattern_type_counts_path: str | Path = PATTERN_TYPE_COUNTS_OUTPUT_PATH,
    top_vehicles_global_path: str | Path = TOP_VEHICLES_GLOBAL_OUTPUT_PATH,
    top_vehicles_by_family_path: str | Path = TOP_VEHICLES_BY_FAMILY_OUTPUT_PATH,
    top_vehicles_by_pattern_path: str | Path = TOP_VEHICLES_BY_PATTERN_OUTPUT_PATH,
    sample_examples_path: str | Path = SAMPLE_EXAMPLES_OUTPUT_PATH,
    sample_size: int = 5000,
    examples_per_pattern: int = 20,
    mode: str = "overwrite",
) -> None:
    """Write deterministic compact CSV outputs for inspection."""

    _write_csv(candidate_sample_dataframe(silver_df, sample_size), candidate_sample_path, mode)
    _write_csv(connector_family_counts_dataframe(silver_df), connector_family_counts_path, mode)
    _write_csv(pattern_type_counts_dataframe(silver_df), pattern_type_counts_path, mode)
    _write_csv(top_vehicles_global_dataframe(silver_df), top_vehicles_global_path, mode)
    _write_csv(top_vehicles_by_family_dataframe(silver_df), top_vehicles_by_family_path, mode)
    _write_csv(top_vehicles_by_pattern_dataframe(silver_df), top_vehicles_by_pattern_path, mode)
    _write_csv(sample_examples_dataframe(silver_df, examples_per_pattern), sample_examples_path, mode)


def write_mvp_outputs(
    silver_df: Any,
    silver_output_path: str | Path = SILVER_OUTPUT_PATH,
    mode: str = "overwrite",
) -> None:
    """Persist full silver Parquet plus compact CSV gold outputs."""

    write_silver_parquet(silver_df, silver_output_path, mode)
    write_gold_csv_outputs(silver_df, mode=mode)


def _extract_right_context(text_normalized: str, char_end: int) -> str:
    after_connector = text_normalized[char_end:].lstrip()
    boundary = _VEHICLE_BOUNDARY_RE.search(after_connector)
    end = boundary.start() if boundary else len(after_connector)
    return after_connector[: min(end, RIGHT_CONTEXT_CHARS)].strip()


def _compact_context(text_before: str, matched_text: str, vehicle_raw: str) -> str:
    parts = [text_before, matched_text, vehicle_raw]
    return _WHITESPACE_RE.sub(" ", " ".join(part for part in parts if part)).strip()


def _candidate_id(
    source_file: str,
    original_line_id: int,
    segment_id: int,
    char_start: int,
    char_end: int,
    pattern_type: str,
    matched_text: str,
) -> str:
    identity = "|".join(
        [
            source_file,
            str(original_line_id),
            str(segment_id),
            str(char_start),
            str(char_end),
            pattern_type,
            matched_text,
        ]
    )
    return hashlib.sha1(identity.encode("utf-8")).hexdigest()


def _top_vehicles_dataframe(silver_df: Any, group_columns: list[str]) -> Any:
    from pyspark.sql.functions import col, count, countDistinct

    grouped_columns = [*group_columns, "vehicle_normalized"]
    order_columns = [col("occurrence_count").desc(), *[col(column) for column in grouped_columns]]

    return (
        silver_df.groupBy(*grouped_columns)
        .agg(
            count("*").alias("occurrence_count"),
            countDistinct("candidate_full_text").alias("distinct_candidate_text_count"),
        )
        .orderBy(*order_columns)
    )


def _write_csv(dataframe: Any, output_path: str | Path, mode: str) -> None:
    dataframe.write.mode(mode).option("header", True).csv(str(output_path))
