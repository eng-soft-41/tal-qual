"""Spec-0006 `ground como article vehicle` extraction helpers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMO_ARTICLE_GROUND_VEHICLE_OUTPUT_PATH = Path("data/gold/como_article_ground_vehicle_candidates")
COMO_ARTICLE_GROUND_VEHICLE_COUNTS_OUTPUT_PATH = Path("outputs/como_article_ground_vehicle_counts.csv")
COMO_ARTICLE_VEHICLE_GROUND_COUNTS_OUTPUT_PATH = Path("outputs/como_article_vehicle_ground_counts.csv")
COMO_ARTICLE_GROUND_COUNTS_OUTPUT_PATH = Path("outputs/como_article_ground_counts.csv")
COMO_ARTICLE_VEHICLE_COUNTS_OUTPUT_PATH = Path("outputs/como_article_vehicle_counts.csv")
COMO_ARTICLE_EXAMPLES_OUTPUT_PATH = Path("outputs/como_article_examples.csv")
COMO_ARTICLE_REVIEW_SAMPLE_OUTPUT_PATH = Path("outputs/como_article_review_sample.csv")

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


def _write_csv(dataframe: Any, output_path: str | Path, mode: str) -> None:
    dataframe.coalesce(1).write.mode(mode).option("header", True).csv(str(output_path))
