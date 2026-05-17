"""Boundary-safe bronze text preparation for brWaC inputs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

RAW_CORPUS_INPUT = Path("data/raw/brwac-clean-1.txt.gz")
RAW_CORPUS_GLOB = Path("data/raw/*.txt.gz")
BRONZE_OUTPUT_PATH = Path("data/bronze/brwac_segments")
END_MARKER = "<END>"

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim surrounding space."""

    return _WHITESPACE_RE.sub(" ", text).strip()


def prepare_bronze_rows(
    source_file: str,
    original_line_id: int,
    raw_text: str,
) -> list[dict[str, object]]:
    """Split one raw corpus line into boundary-safe bronze segment rows."""

    rows: list[dict[str, object]] = []

    for raw_segment in raw_text.split(END_MARKER):
        text_original = raw_segment.strip()
        text_normalized = normalize_whitespace(raw_segment)

        if not text_normalized:
            continue

        rows.append(
            {
                "source_file": source_file,
                "original_line_id": original_line_id,
                "segment_id": len(rows),
                "text_original": text_original,
                "text_normalized": text_normalized,
                "match_text": text_normalized.lower(),
            }
        )

    return rows


def read_raw_corpus(spark: Any, input_path: str | Path) -> Any:
    """Read gzipped brWaC text and attach source and line provenance."""

    from pyspark.sql.functions import col, input_file_name, monotonically_increasing_id

    return spark.read.text(str(input_path)).select(
        input_file_name().alias("source_file"),
        monotonically_increasing_id().alias("original_line_id"),
        col("value").alias("raw_text"),
    )


def prepare_bronze_dataframe(spark: Any, input_path: str | Path) -> Any:
    """Create the bronze segment DataFrame from gzipped raw corpus input."""

    from pyspark.sql.functions import col, lower, posexplode, regexp_replace, split, trim

    raw_df = repartition_raw_corpus_dataframe(spark, read_raw_corpus(spark, input_path))

    exploded_df = raw_df.select(
        "source_file",
        "original_line_id",
        posexplode(split(col("raw_text"), END_MARKER)).alias("segment_id", "raw_segment"),
    )

    text_original = trim(col("raw_segment"))
    text_normalized = trim(regexp_replace(col("raw_segment"), r"\s+", " "))

    return (
        exploded_df.select(
            "source_file",
            "original_line_id",
            "segment_id",
            text_original.alias("text_original"),
            text_normalized.alias("text_normalized"),
            lower(text_normalized).alias("match_text"),
        )
        .where(col("text_normalized") != "")
    )


def write_bronze_parquet(
    bronze_df: Any,
    output_path: str | Path = BRONZE_OUTPUT_PATH,
    mode: str = "overwrite",
) -> None:
    """Write bronze rows as Spark Parquet."""

    bronze_df.write.mode(mode).parquet(str(output_path))


def read_bronze_parquet(spark: Any, output_path: str | Path = BRONZE_OUTPUT_PATH) -> Any:
    """Read materialized bronze rows from Spark Parquet."""

    return spark.read.parquet(str(output_path))


def load_or_build_bronze_dataframe(
    spark: Any,
    input_path: str | Path = RAW_CORPUS_INPUT,
    output_path: str | Path = BRONZE_OUTPUT_PATH,
) -> Any:
    """Load bronze parquet, or build it and reload it to cut raw-corpus lineage."""

    output_path = Path(output_path)
    if output_path.exists():
        return read_bronze_parquet(spark, output_path)

    write_bronze_parquet(prepare_bronze_dataframe(spark, input_path), output_path)
    return read_bronze_parquet(spark, output_path)


def repartition_raw_corpus_dataframe(spark: Any, raw_df: Any) -> Any:
    """Spread raw lines before CPU-heavy normalization when Spark has parallelism."""

    parallelism = int(getattr(spark.sparkContext, "defaultParallelism", 1))
    if parallelism <= 1:
        return raw_df
    return raw_df.repartition(parallelism)
