"""Silver candidate extraction for narrow Portuguese comparison connectors."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

LEFT_CONTEXT_CHARS = 80
RIGHT_CONTEXT_CHARS = 120

_VEHICLE_BOUNDARY_RE = re.compile(r"<END>|[,.!?;:]")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ConnectorPattern:
    connector_family: str
    pattern_type: str
    comparison_form: str
    regex: re.Pattern[str]


CONNECTOR_PATTERNS: tuple[ConnectorPattern, ...] = (
    ConnectorPattern("como", "como_article", "nominal", re.compile(r"\bcomo\s+um(?:a|as|s)?\b")),
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
        re.compile(r"\bigualzinh(?:o|a|os|as)\s+um(?:a|as|s)?\b"),
    ),
    ConnectorPattern(
        "igual",
        "igual_preposition",
        "prepositional",
        re.compile(r"\bigual\s+(?:a|ao|à|aos|às)\b"),
    ),
    ConnectorPattern("igual", "igual_article", "nominal", re.compile(r"\bigual\s+um(?:a|as|s)?\b")),
)


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
