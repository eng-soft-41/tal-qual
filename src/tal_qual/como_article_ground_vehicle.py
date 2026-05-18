"""Spec-0006 `ground como article vehicle` extraction helpers."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMO_ARTICLE_GROUND_VEHICLE_OUTPUT_PATH = Path("data/gold/como_article_ground_vehicle_candidates")
COMO_ARTICLE_GROUND_VEHICLE_COUNTS_OUTPUT_PATH = Path("outputs/como_article_ground_vehicle_counts.csv")
COMO_ARTICLE_VEHICLE_GROUND_COUNTS_OUTPUT_PATH = Path("outputs/como_article_vehicle_ground_counts.csv")
COMO_ARTICLE_GROUND_COUNTS_OUTPUT_PATH = Path("outputs/como_article_ground_counts.csv")
COMO_ARTICLE_VEHICLE_COUNTS_OUTPUT_PATH = Path("outputs/como_article_vehicle_counts.csv")
COMO_ARTICLE_EXAMPLES_OUTPUT_PATH = Path("outputs/como_article_examples.csv")
COMO_ARTICLE_REVIEW_SAMPLE_OUTPUT_PATH = Path("outputs/como_article_review_sample.csv")
COMO_ARTICLE_BACKEND_EXPORT_DIR = Path("data/export/backend/comparisons/v1")
COMO_ARTICLE_BACKEND_CANDIDATES_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "candidates.jsonl"
COMO_ARTICLE_BACKEND_GROUND_VEHICLE_COUNTS_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "ground_vehicle_counts.json"
COMO_ARTICLE_BACKEND_VEHICLE_GROUND_COUNTS_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "vehicle_ground_counts.json"
COMO_ARTICLE_BACKEND_GROUND_COUNTS_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "ground_counts.json"
COMO_ARTICLE_BACKEND_VEHICLE_COUNTS_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "vehicle_counts.json"
COMO_ARTICLE_BACKEND_EXAMPLES_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "examples.jsonl"
COMO_ARTICLE_BACKEND_MANIFEST_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "manifest.json"
COMO_ARTICLE_BACKEND_REVIEW_SAMPLE_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "review_sample.jsonl"
COMO_ARTICLE_BACKEND_REJECTED_OR_REVIEW_PATH = COMO_ARTICLE_BACKEND_EXPORT_DIR / "rejected_or_review_candidates.jsonl"

DATASET_VERSION = "v1"
BACKEND_DATASET_NAME = "tal-qual-comparisons"
BACKEND_SCHEMA_VERSION = 1

LEFT_CONTEXT_CHARS = 80
MAX_VEHICLE_TOKENS = 5

_WHITESPACE_RE = re.compile(r"\s+")
_BOUNDARY_RE = re.compile(r"[,.!?;:]|<END>", re.IGNORECASE)
_WORD_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ'-]+")
_CONNECTOR_RE = re.compile(r"\bcomo\s+(?:um|uma|uns|umas)\b", re.IGNORECASE)

_QUALITY_LEMMAS = frozenset(
    {
        "forte",
        "fraco",
        "leve",
        "pesado",
        "grande",
        "pequeno",
        "rápido",
        "lento",
        "duro",
        "mole",
        "frio",
        "quente",
        "claro",
        "escuro",
        "brilhante",
        "cego",
        "livre",
        "preso",
        "frágil",
        "seco",
        "doce",
        "amargo",
        "limpo",
        "sujo",
        "alto",
        "baixo",
        "calmo",
        "alegre",
        "triste",
        "vazio",
        "cheio",
    }
)
_QUALITY_FORMS = {
    "forte": "forte",
    "fortes": "forte",
    "fraco": "fraco",
    "fraca": "fraco",
    "fracos": "fraco",
    "fracas": "fraco",
    "leve": "leve",
    "leves": "leve",
    "pesado": "pesado",
    "pesada": "pesado",
    "pesados": "pesado",
    "pesadas": "pesado",
    "grande": "grande",
    "grandes": "grande",
    "pequeno": "pequeno",
    "pequena": "pequeno",
    "pequenos": "pequeno",
    "pequenas": "pequeno",
    "rápido": "rápido",
    "rápida": "rápido",
    "rápidos": "rápido",
    "rápidas": "rápido",
    "lento": "lento",
    "lenta": "lento",
    "lentos": "lento",
    "lentas": "lento",
    "duro": "duro",
    "dura": "duro",
    "duros": "duro",
    "duras": "duro",
    "mole": "mole",
    "moles": "mole",
    "frio": "frio",
    "fria": "frio",
    "frios": "frio",
    "frias": "frio",
    "quente": "quente",
    "quentes": "quente",
    "claro": "claro",
    "clara": "claro",
    "claros": "claro",
    "claras": "claro",
    "escuro": "escuro",
    "escura": "escuro",
    "escuros": "escuro",
    "escuras": "escuro",
    "brilhante": "brilhante",
    "brilhantes": "brilhante",
    "cego": "cego",
    "cega": "cego",
    "cegos": "cego",
    "cegas": "cego",
    "livre": "livre",
    "livres": "livre",
    "preso": "preso",
    "presa": "preso",
    "presos": "preso",
    "presas": "preso",
    "frágil": "frágil",
    "frágeis": "frágil",
    "seco": "seco",
    "seca": "seco",
    "secos": "seco",
    "secas": "seco",
    "doce": "doce",
    "doces": "doce",
    "amargo": "amargo",
    "amarga": "amargo",
    "amargos": "amargo",
    "amargas": "amargo",
    "limpo": "limpo",
    "limpa": "limpo",
    "limpos": "limpo",
    "limpas": "limpo",
    "sujo": "sujo",
    "suja": "sujo",
    "sujos": "sujo",
    "sujas": "sujo",
    "alto": "alto",
    "alta": "alto",
    "altos": "alto",
    "altas": "alto",
    "baixo": "baixo",
    "baixa": "baixo",
    "baixos": "baixo",
    "baixas": "baixo",
    "calmo": "calmo",
    "calma": "calmo",
    "calmos": "calmo",
    "calmas": "calmo",
    "alegre": "alegre",
    "alegres": "alegre",
    "triste": "triste",
    "tristes": "triste",
    "vazio": "vazio",
    "vazia": "vazio",
    "vazios": "vazio",
    "vazias": "vazio",
    "cheio": "cheio",
    "cheia": "cheio",
    "cheios": "cheio",
    "cheias": "cheio",
}

_VERB_FORMS = {
    "cair": "cair",
    "caiu": "cair",
    "cai": "cair",
    "cairia": "cair",
    "voar": "voar",
    "voa": "voar",
    "voou": "voar",
    "voava": "voar",
    "flutuar": "flutuar",
    "flutua": "flutuar",
    "flutuou": "flutuar",
    "flutue": "flutuar",
    "correr": "correr",
    "corre": "correr",
    "correu": "correr",
    "corria": "correr",
    "brilhar": "brilhar",
    "brilha": "brilhar",
    "brilhou": "brilhar",
    "brilhava": "brilhar",
    "trabalhar": "trabalhar",
    "trabalha": "trabalhar",
    "trabalhou": "trabalhar",
    "trabalhava": "trabalhar",
    "encaixar": "encaixar",
    "encaixa": "encaixar",
    "encaixou": "encaixar",
    "caber": "caber",
    "cabe": "caber",
    "coube": "caber",
    "assentar": "assentar",
    "assenta": "assentar",
    "assentou": "assentar",
}

_GROUND_FORMS = _QUALITY_FORMS | _VERB_FORMS
_GROUND_WORD = "|".join(re.escape(word) for word in sorted(_GROUND_FORMS, key=len, reverse=True))
_COMO_ARTICLE_GROUND_RE = re.compile(
    rf"\b(?P<ground>{_GROUND_WORD})\s+(?P<connector>como\s+(?:um|uma|uns|umas))\b",
    re.IGNORECASE,
)
_SPARK_PREFILTER_RE = rf"\b(?:{_GROUND_WORD})\s+como\s+(?:um|uma|uns|umas)\b"

_BAD_VEHICLE_STARTS = frozenset(
    {
        "de",
        "do",
        "da",
        "dos",
        "das",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "o",
        "a",
        "os",
        "as",
        "ele",
        "ela",
        "eu",
        "me",
        "todo",
        "toda",
        "todos",
        "todas",
        "é",
        "foi",
        "parece",
        "quando",
        "sempre",
        "só",
    }
)
_GENERIC_VEHICLE_HEADS = frozenset(
    {
        "coisa",
        "forma",
        "tipo",
        "espécie",
        "parte",
        "meio",
        "processo",
        "exemplo",
        "tema",
    }
)
_ROLE_CONTEXT_RE = re.compile(
    r"\b(?:usad\w*|utilizad\w*|conhecid\w*|tratad\w*|considerad\w*|definid\w*|"
    r"classificad\w*|entendid\w*)\b",
    re.IGNORECASE,
)
_NOISE_RE = re.compile(r"https?://|www\.|[@#]|\d+%|^\d+$", re.IGNORECASE)
_CLEANUP_HEADS = frozenset(
    {
        "luva",
        "bomba",
        "raio",
        "pedra",
        "rocha",
        "pluma",
        "touro",
        "flecha",
        "borboleta",
        "pássaro",
        "avião",
    }
)
_CLAUSE_STARTS = frozenset({"é", "foi", "era", "fica", "tem", "deve", "ele", "ela", "isso"})


@dataclass(frozen=True)
class VehicleExtraction:
    text: str
    tokens: tuple[str, ...]
    start: int
    end: int
    too_long: bool


def extract_como_article_ground_vehicle_rows(
    source_file: str,
    original_line_id: int,
    segment_id: int,
    text_normalized: str,
    match_text: str | None = None,
) -> list[dict[str, object]]:
    """Extract kept spec-0006 candidates from one bronze segment."""

    searchable = match_text if match_text is not None else text_normalized.lower()
    rows: list[dict[str, object]] = []

    for match in _COMO_ARTICLE_GROUND_RE.finditer(searchable):
        ground_text = text_normalized[match.start("ground") : match.end("ground")]
        connector = text_normalized[match.start("connector") : match.end("connector")]
        text_before = text_normalized[: match.start("ground")].rstrip()[-LEFT_CONTEXT_CHARS:].lstrip()
        vehicle = _extract_vehicle(text_normalized, match.end("connector"))
        ground_type, ground_source = _ground_class(ground_text)
        ground_lemma = _GROUND_FORMS[ground_text.lower()]
        vehicle_head = vehicle.tokens[0] if vehicle.tokens else ""
        reject_reason = _reject_reason(ground_text, vehicle, text_before)
        if reject_reason:
            continue

        matched_text = text_normalized[match.start("ground") : match.end("connector")]
        rows.append(
            {
                "candidate_id": _candidate_id(
                    source_file,
                    original_line_id,
                    segment_id,
                    match.start("ground"),
                    vehicle.end,
                    "como_article_ground_vehicle",
                ),
                "source_file": source_file,
                "original_line_id": original_line_id,
                "segment_id": segment_id,
                "pattern_type": "como_article_ground_vehicle",
                "connector": connector,
                "connector_text": connector,
                "matched_text": matched_text,
                "candidate_full_text": _compact_text(text_before, matched_text, vehicle.text),
                "text_before": text_before,
                "tenor_text": _fallback_tenor(text_before),
                "tenor_lemma": _fallback_tenor(text_before).lower(),
                "tenor_confidence": "fallback_left_context" if text_before else "missing",
                "ground_text": ground_text,
                "ground_lemma": ground_lemma,
                "ground_type": ground_type,
                "ground_source": ground_source,
                "vehicle_text": vehicle.text,
                "vehicle_lemma": vehicle.text.lower(),
                "vehicle_head": vehicle_head,
                "vehicle_head_lemma": vehicle_head.lower(),
                "vehicle_phrase_length_tokens": len(vehicle.tokens),
                "filter_label": "keep",
                "reject_reason": "",
                "confidence": _confidence(text_before, len(vehicle.tokens)),
                "needs_review": not text_before,
                "char_start": match.start("ground"),
                "char_end": vehicle.end,
                "connector_start": match.start("connector"),
                "connector_end": match.end("connector"),
                "vehicle_start": vehicle.start,
                "vehicle_end": vehicle.end,
            }
        )

    return sorted(rows, key=lambda row: (row["char_start"], row["char_end"], row["candidate_id"]))


def prepare_como_article_ground_vehicle_dataframe(bronze_df: Any) -> Any:
    """Create spec-0006 candidates from bronze segments."""

    from pyspark.sql.functions import col, explode, udf
    from pyspark.sql.types import BooleanType, DoubleType, IntegerType, LongType, StringType, StructField, StructType, ArrayType

    schema = ArrayType(
        StructType(
            [
                StructField("candidate_id", StringType(), nullable=False),
                StructField("source_file", StringType(), nullable=False),
                StructField("original_line_id", LongType(), nullable=False),
                StructField("segment_id", IntegerType(), nullable=False),
                StructField("pattern_type", StringType(), nullable=False),
                StructField("connector", StringType(), nullable=False),
                StructField("connector_text", StringType(), nullable=False),
                StructField("matched_text", StringType(), nullable=False),
                StructField("candidate_full_text", StringType(), nullable=False),
                StructField("text_before", StringType(), nullable=False),
                StructField("tenor_text", StringType(), nullable=False),
                StructField("tenor_lemma", StringType(), nullable=False),
                StructField("tenor_confidence", StringType(), nullable=False),
                StructField("ground_text", StringType(), nullable=False),
                StructField("ground_lemma", StringType(), nullable=False),
                StructField("ground_type", StringType(), nullable=False),
                StructField("ground_source", StringType(), nullable=False),
                StructField("vehicle_text", StringType(), nullable=False),
                StructField("vehicle_lemma", StringType(), nullable=False),
                StructField("vehicle_head", StringType(), nullable=False),
                StructField("vehicle_head_lemma", StringType(), nullable=False),
                StructField("vehicle_phrase_length_tokens", IntegerType(), nullable=False),
                StructField("filter_label", StringType(), nullable=False),
                StructField("reject_reason", StringType(), nullable=False),
                StructField("confidence", DoubleType(), nullable=False),
                StructField("needs_review", BooleanType(), nullable=False),
                StructField("char_start", IntegerType(), nullable=False),
                StructField("char_end", IntegerType(), nullable=False),
                StructField("connector_start", IntegerType(), nullable=False),
                StructField("connector_end", IntegerType(), nullable=False),
                StructField("vehicle_start", IntegerType(), nullable=False),
                StructField("vehicle_end", IntegerType(), nullable=False),
            ]
        )
    )
    extract_rows = udf(extract_como_article_ground_vehicle_rows, schema)

    return bronze_df.withColumn(
        "candidate",
        explode(
            extract_rows(
                col("source_file"),
                col("original_line_id"),
                col("segment_id"),
                col("text_normalized"),
                col("match_text"),
            )
        ),
    ).select("candidate.*")


def prefilter_como_article_ground_vehicle_bronze_dataframe(bronze_df: Any) -> Any:
    """Return bronze rows that can possibly match spec-0006 before Python UDF extraction."""

    from pyspark.sql.functions import col

    return bronze_df.where(col("match_text").rlike(_SPARK_PREFILTER_RE))


def write_como_article_ground_vehicle_parquet(
    candidates_df: Any,
    output_path: str | Path = COMO_ARTICLE_GROUND_VEHICLE_OUTPUT_PATH,
    mode: str = "overwrite",
) -> None:
    candidates_df.write.mode(mode).parquet(str(output_path))


def write_como_article_csv_outputs(
    candidates_df: Any,
    ground_vehicle_counts_path: str | Path = COMO_ARTICLE_GROUND_VEHICLE_COUNTS_OUTPUT_PATH,
    vehicle_ground_counts_path: str | Path = COMO_ARTICLE_VEHICLE_GROUND_COUNTS_OUTPUT_PATH,
    ground_counts_path: str | Path = COMO_ARTICLE_GROUND_COUNTS_OUTPUT_PATH,
    vehicle_counts_path: str | Path = COMO_ARTICLE_VEHICLE_COUNTS_OUTPUT_PATH,
    examples_path: str | Path = COMO_ARTICLE_EXAMPLES_OUTPUT_PATH,
    review_sample_path: str | Path = COMO_ARTICLE_REVIEW_SAMPLE_OUTPUT_PATH,
    mode: str = "overwrite",
) -> None:
    _write_csv(como_article_ground_vehicle_counts_dataframe(candidates_df), ground_vehicle_counts_path, mode)
    _write_csv(como_article_vehicle_ground_counts_dataframe(candidates_df), vehicle_ground_counts_path, mode)
    _write_csv(como_article_ground_counts_dataframe(candidates_df), ground_counts_path, mode)
    _write_csv(como_article_vehicle_counts_dataframe(candidates_df), vehicle_counts_path, mode)
    _write_csv(como_article_examples_dataframe(candidates_df), examples_path, mode)
    _write_csv(como_article_review_sample_dataframe(candidates_df), review_sample_path, mode)


def cleanup_como_article_backend_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Return one candidate row enriched with backend export cleanup metadata."""

    enriched = dict(row)
    vehicle_raw = str(enriched.get("vehicle_text_raw") or enriched.get("vehicle_text") or "")
    raw_tokens = _word_tokens(vehicle_raw)
    clean_tokens = list(raw_tokens)
    cleaning_rule = "unchanged"
    tail_tokens: list[str] = []
    quality_reasons: list[str] = []

    if len(raw_tokens) > 1:
        clause_index = next((index for index, token in enumerate(raw_tokens[1:], start=1) if token.lower() in _CLAUSE_STARTS), None)
        if clause_index is not None:
            clean_tokens = raw_tokens[:clause_index]
            tail_tokens = raw_tokens[clause_index:]
            cleaning_rule = "trimmed_clause_start"
            quality_reasons.append("trimmed_clause_start")
        elif raw_tokens[0].lower() in _CLEANUP_HEADS:
            clean_tokens = [raw_tokens[0]]
            tail_tokens = raw_tokens[1:]
            cleaning_rule = "trimmed_common_head_tail"
            quality_reasons.append("trimmed_common_head_tail")

    vehicle_text_clean = _compact_text(*clean_tokens)
    vehicle_tail_text = _compact_text(*tail_tokens)
    vehicle_head_clean = clean_tokens[0] if clean_tokens else str(enriched.get("vehicle_head") or "")
    vehicle_head_clean_lemma = vehicle_head_clean.lower()
    vehicle_clean_lemma = vehicle_text_clean.lower()

    existing_reject_reason = str(enriched.get("reject_reason") or "")
    if existing_reject_reason:
        quality_label = "reject"
        quality_reasons.append(existing_reject_reason)
    elif _ROLE_CONTEXT_RE.search(
        _compact_text(
            str(enriched.get("text_before") or ""),
            str(enriched.get("ground_text") or ""),
            str(enriched.get("candidate_full_text") or ""),
        )
    ):
        quality_label = "review"
        quality_reasons.append("role_or_classification_context")
    elif cleaning_rule != "unchanged":
        quality_label = "trimmed"
    else:
        quality_label = "keep"

    enriched.update(
        {
            "dataset_version": DATASET_VERSION,
            "vehicle_text_raw": vehicle_raw,
            "vehicle_text_clean": vehicle_text_clean,
            "vehicle_tail_text": vehicle_tail_text,
            "vehicle_cleaning_rule": cleaning_rule,
            "vehicle_lemma": str(enriched.get("vehicle_lemma") or vehicle_raw.lower()),
            "vehicle_head_clean": vehicle_head_clean,
            "vehicle_head_clean_lemma": vehicle_head_clean_lemma,
            "quality_label": quality_label,
            "quality_reason": quality_reasons,
            "visualization_ready": quality_label in {"keep", "trimmed"},
            "needs_review": bool(enriched.get("needs_review")) or quality_label == "review",
        }
    )
    if "vehicle_head_lemma" not in enriched:
        enriched["vehicle_head_lemma"] = vehicle_head_clean_lemma
    if "vehicle_head" not in enriched:
        enriched["vehicle_head"] = vehicle_head_clean
    if vehicle_clean_lemma and "vehicle_text_clean_lemma" not in enriched:
        enriched["vehicle_text_clean_lemma"] = vehicle_clean_lemma
    return enriched


def prepare_como_article_backend_export_dataframe(candidates_df: Any) -> Any:
    """Append backend cleanup fields to a Spark candidates DataFrame."""

    from pyspark.sql.functions import col, struct, udf
    from pyspark.sql.types import ArrayType, BooleanType, StringType, StructField, StructType

    schema = StructType(
        [
            StructField("dataset_version", StringType(), nullable=False),
            StructField("vehicle_text_raw", StringType(), nullable=False),
            StructField("vehicle_text_clean", StringType(), nullable=False),
            StructField("vehicle_tail_text", StringType(), nullable=False),
            StructField("vehicle_cleaning_rule", StringType(), nullable=False),
            StructField("vehicle_head_clean", StringType(), nullable=False),
            StructField("vehicle_head_clean_lemma", StringType(), nullable=False),
            StructField("quality_label", StringType(), nullable=False),
            StructField("quality_reason", ArrayType(StringType()), nullable=False),
            StructField("visualization_ready", BooleanType(), nullable=False),
            StructField("needs_review", BooleanType(), nullable=False),
        ]
    )

    def cleanup_struct(row: Any) -> dict[str, Any]:
        cleaned = cleanup_como_article_backend_candidate(row.asDict(recursive=True))
        return {field.name: cleaned[field.name] for field in schema.fields}

    cleanup = udf(cleanup_struct, schema)
    enriched = candidates_df.withColumn("_backend_cleanup", cleanup(struct("*")))
    for field in schema.fieldNames():
        enriched = enriched.withColumn(field, col(f"_backend_cleanup.{field}"))
    return enriched.drop("_backend_cleanup")


def write_como_article_backend_export(
    candidates: Any,
    export_dir: str | Path = COMO_ARTICLE_BACKEND_EXPORT_DIR,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write backend JSONL/JSON assets from Spark rows or Python dictionaries."""

    rows = [_row_to_dict(row) for row in _collect_rows(candidates)]
    cleaned_rows = [cleanup_como_article_backend_candidate(row) for row in rows]
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    _write_jsonl(export_path / "candidates.jsonl", (_backend_candidate_record(row) for row in cleaned_rows))
    _write_json(export_path / "ground_vehicle_counts.json", _pair_counts(cleaned_rows, "ground_lemma", "vehicle_head_clean_lemma"))
    _write_json(export_path / "vehicle_ground_counts.json", _pair_counts(cleaned_rows, "vehicle_head_clean_lemma", "ground_lemma"))
    ground_counts = _single_counts(cleaned_rows, "ground_lemma", "vehicle_head_clean_lemma", "top_vehicle")
    vehicle_counts = _single_counts(cleaned_rows, "vehicle_head_clean_lemma", "ground_lemma", "top_ground")
    _write_json(export_path / "ground_counts.json", ground_counts)
    _write_json(export_path / "vehicle_counts.json", vehicle_counts)
    _write_jsonl(export_path / "examples.jsonl", (_example_record(row) for row in cleaned_rows[:5000]))
    review_rows = [row for row in cleaned_rows if row.get("needs_review")]
    rejected_or_review_rows = [row for row in cleaned_rows if row.get("quality_label") in {"reject", "review"}]
    _write_jsonl(export_path / "review_sample.jsonl", (_backend_candidate_record(row) for row in review_rows[:500]))
    _write_jsonl(export_path / "rejected_or_review_candidates.jsonl", (_backend_candidate_record(row) for row in rejected_or_review_rows))

    manifest = {
        "dataset_name": BACKEND_DATASET_NAME,
        "dataset_version": DATASET_VERSION,
        "pattern_type": "como_article_ground_vehicle",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "source_gold_path": str(COMO_ARTICLE_GROUND_VEHICLE_OUTPUT_PATH),
        "candidate_count": len(cleaned_rows),
        "visualization_ready_count": sum(1 for row in cleaned_rows if row.get("visualization_ready")),
        "ground_count": len({row.get("ground_lemma") for row in cleaned_rows if row.get("ground_lemma")}),
        "vehicle_count": len({row.get("vehicle_head_clean_lemma") for row in cleaned_rows if row.get("vehicle_head_clean_lemma")}),
        "ground_vehicle_pair_count": len(
            {
                (row.get("ground_lemma"), row.get("vehicle_head_clean_lemma"))
                for row in cleaned_rows
                if row.get("ground_lemma") and row.get("vehicle_head_clean_lemma")
            }
        ),
        "schema_version": BACKEND_SCHEMA_VERSION,
    }
    _write_json(export_path / "manifest.json", manifest)
    return manifest


def como_article_ground_vehicle_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.groupBy("ground_lemma", "vehicle_head_lemma")
        .count()
        .orderBy(col("count").desc(), col("ground_lemma"), col("vehicle_head_lemma"))
    )


def como_article_vehicle_ground_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.groupBy("vehicle_head_lemma", "ground_lemma")
        .count()
        .orderBy(col("count").desc(), col("vehicle_head_lemma"), col("ground_lemma"))
    )


def como_article_ground_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return candidates_df.groupBy("ground_lemma").count().orderBy(col("count").desc(), col("ground_lemma"))


def como_article_vehicle_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return candidates_df.groupBy("vehicle_head_lemma").count().orderBy(col("count").desc(), col("vehicle_head_lemma"))


def como_article_examples_dataframe(candidates_df: Any, limit: int = 5000) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.select("ground_text", "connector_text", "vehicle_text", "tenor_text", "candidate_full_text")
        .orderBy(col("ground_lemma"), col("vehicle_head_lemma"), col("candidate_id"))
        .limit(limit)
    )


def como_article_review_sample_dataframe(candidates_df: Any, limit: int = 500) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.select(
            "candidate_id",
            "ground_type",
            "ground_text",
            "connector_text",
            "vehicle_text",
            "tenor_text",
            "confidence",
            "needs_review",
            "candidate_full_text",
        )
        .orderBy(col("needs_review").desc(), col("confidence"), col("candidate_id"))
        .limit(limit)
    )


def _extract_vehicle(text: str, start: int) -> VehicleExtraction:
    right = text[start:]
    leading = len(right) - len(right.lstrip())
    phrase_start = start + leading
    trimmed = right.lstrip()
    boundary = _BOUNDARY_RE.search(trimmed)
    phrase_raw = trimmed[: boundary.start() if boundary else len(trimmed)]
    tokens = tuple(_word_tokens(phrase_raw))
    if not tokens:
        return VehicleExtraction("", (), phrase_start, phrase_start, too_long=False)
    selected = tokens[:MAX_VEHICLE_TOKENS]
    phrase_text = _compact_text(*selected)
    last_match = None
    for index, token_match in enumerate(_WORD_RE.finditer(phrase_raw)):
        if index == len(selected) - 1:
            last_match = token_match
            break
    phrase_end = phrase_start + (last_match.end() if last_match else 0)
    return VehicleExtraction(phrase_text, selected, phrase_start, phrase_end, too_long=len(tokens) > MAX_VEHICLE_TOKENS)


def _reject_reason(ground: str, vehicle: VehicleExtraction, text_before: str) -> str:
    if not ground or not vehicle.tokens:
        return "missing_ground_or_vehicle"
    if vehicle.too_long:
        return "vehicle_too_long"
    head = vehicle.tokens[0].lower()
    if not head[0].isalpha():
        return "bad_vehicle_start"
    if head in _BAD_VEHICLE_STARTS:
        return "bad_vehicle_start"
    if head in _GENERIC_VEHICLE_HEADS:
        return "generic_vehicle_head"
    if _NOISE_RE.search(vehicle.text) or any(_NOISE_RE.search(token) for token in vehicle.tokens):
        return "vehicle_noise"
    if _ROLE_CONTEXT_RE.search(_compact_text(text_before, ground)):
        return "role_or_classification_context"
    return ""


def _ground_class(ground_text: str) -> tuple[str, str]:
    normalized = ground_text.lower()
    lemma = _GROUND_FORMS[normalized]
    if lemma in _QUALITY_LEMMAS:
        return "quality_adjective", "curated_quality_list"
    return "salient_verb", "curated_verb_list"


def _fallback_tenor(text_before: str) -> str:
    return _compact_text(*_word_tokens(text_before)[-5:])


def _confidence(text_before: str, vehicle_token_count: int) -> float:
    if not text_before:
        return 0.75
    if vehicle_token_count == 1:
        return 0.95
    return 0.9


def _word_tokens(text: str) -> list[str]:
    return [token for token in _WORD_RE.findall(text) if any(character.isalnum() for character in token)]


def _compact_text(*parts: str) -> str:
    return _WHITESPACE_RE.sub(" ", " ".join(part for part in parts if part)).strip()


def _candidate_id(
    source_file: str,
    original_line_id: int,
    segment_id: int,
    char_start: int,
    char_end: int,
    pattern_type: str,
) -> str:
    identity = "|".join([source_file, str(original_line_id), str(segment_id), str(char_start), str(char_end), pattern_type])
    return hashlib.sha1(identity.encode("utf-8")).hexdigest()


_BACKEND_CANDIDATE_FIELDS = (
    "candidate_id",
    "dataset_version",
    "pattern_type",
    "connector_text",
    "candidate_full_text",
    "text_before",
    "tenor_text",
    "tenor_lemma",
    "tenor_confidence",
    "ground_text",
    "ground_lemma",
    "ground_type",
    "ground_source",
    "vehicle_text_raw",
    "vehicle_text_clean",
    "vehicle_tail_text",
    "vehicle_cleaning_rule",
    "vehicle_lemma",
    "vehicle_head",
    "vehicle_head_lemma",
    "vehicle_head_clean",
    "vehicle_head_clean_lemma",
    "vehicle_phrase_length_tokens",
    "quality_label",
    "quality_reason",
    "visualization_ready",
    "confidence",
    "needs_review",
    "source_file",
    "original_line_id",
    "segment_id",
    "char_start",
    "char_end",
    "connector_start",
    "connector_end",
    "vehicle_start",
    "vehicle_end",
)


def _collect_rows(candidates: Any) -> list[Any]:
    if hasattr(candidates, "collect"):
        return list(candidates.collect())
    return list(candidates)


def _row_to_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "asDict"):
        return row.asDict(recursive=True)
    return dict(row)


def _backend_candidate_record(row: dict[str, Any]) -> dict[str, Any]:
    return {field: _json_value(row.get(field)) for field in _BACKEND_CANDIDATE_FIELDS}


def _example_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": row.get("candidate_id"),
        "ground_text": row.get("ground_text"),
        "connector_text": row.get("connector_text"),
        "vehicle_text_clean": row.get("vehicle_text_clean"),
        "tenor_text": row.get("tenor_text"),
        "candidate_full_text": row.get("candidate_full_text"),
    }


def _pair_counts(rows: list[dict[str, Any]], first_key: str, second_key: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        first = str(row.get(first_key) or "")
        second = str(row.get(second_key) or "")
        if first and second:
            groups[(first, second)].append(str(row.get("candidate_id") or ""))
    first_name = first_key
    second_name = second_key
    return [
        {
            first_name: first,
            second_name: second,
            "count": len(candidate_ids),
            "example_candidate_ids": candidate_ids[:5],
        }
        for (first, second), candidate_ids in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0][0], item[0][1]))
    ]


def _single_counts(rows: list[dict[str, Any]], key: str, distinct_key: str, top_prefix: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = str(row.get(key) or "")
        if value:
            grouped[value].append(row)

    records = []
    for value, group_rows in grouped.items():
        related_counts = Counter(str(row.get(distinct_key) or "") for row in group_rows if row.get(distinct_key))
        if not related_counts:
            continue
        top_value, top_count = sorted(related_counts.items(), key=lambda item: (-item[1], item[0]))[0]
        count = len(group_rows)
        record = {
            key: value,
            "count": count,
            f"distinct_{'vehicle' if distinct_key == 'vehicle_head_clean_lemma' else 'ground'}_count": len(related_counts),
            f"{top_prefix}_{'head_clean_lemma' if top_prefix == 'top_vehicle' else 'lemma'}": top_value,
            f"{top_prefix}_count": top_count,
            f"{top_prefix}_share": round(top_count / count, 4) if count else 0,
        }
        records.append(record)
    return sorted(records, key=lambda record: (-int(record["count"]), str(record[key])))


def _write_jsonl(path: Path, records: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    return value


def _write_csv(dataframe: Any, output_path: str | Path, mode: str) -> None:
    dataframe.coalesce(1).write.mode(mode).option("header", True).csv(str(output_path))
