"""Spec-0007 dataset expansion experiment helpers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tal_qual.como_article_ground_vehicle import _GROUND_FORMS, _QUALITY_LEMMAS

EXPERIMENT_DATASET_ROOT = Path("data/gold/experiments")
EXPERIMENT_OUTPUT_ROOT = Path("outputs/experiments")
EVALUATION_DATASET_PATH = Path("data/gold/evaluation/como_article_strategy_candidates")
EVALUATION_OUTPUT_ROOT = Path("outputs/evaluation")

LEFT_CONTEXT_CHARS = 80
MAX_EXPERIMENT_VEHICLE_TOKENS = 4

EXPERIMENT_SLUGS = (
    "bare_como_curated_ground",
    "bare_como_curated_ground_v2",
    "colloquial_que_nem_feito",
    "broader_ground_window_como_article",
)

_GROUND_WORD = "|".join(re.escape(word) for word in sorted(_GROUND_FORMS, key=len, reverse=True))
_QUALITY_FORMS = {form: lemma for form, lemma in _GROUND_FORMS.items() if lemma in _QUALITY_LEMMAS}
_QUALITY_WORD = "|".join(re.escape(word) for word in sorted(_QUALITY_FORMS, key=len, reverse=True))
_WORD_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ'-]+")
_WHITESPACE_RE = re.compile(r"\s+")
_BOUNDARY_RE = re.compile(r"[,.!?;:]|<END>", re.IGNORECASE)

_BARE_COMO_RE = re.compile(
    rf"\b(?P<ground>{_QUALITY_WORD})\s+(?P<connector>como)\s+(?!(?:um|uma|uns|umas)\b)",
    re.IGNORECASE,
)
_COLLOQUIAL_RE = re.compile(
    rf"\b(?P<ground>{_GROUND_WORD})\s+(?P<connector>que\s+nem|feito|feita|feitos|feitas)\b",
    re.IGNORECASE,
)
_COMO_ARTICLE_WINDOW_RE = re.compile(
    rf"\b(?:(?:tão|tao|mais|menos|muito|bem|quase|bastante)\s+)?"
    rf"(?P<ground>{_GROUND_WORD})\s+(?P<connector>como\s+(?:um|uma|uns|umas))\b",
    re.IGNORECASE,
)

_EXPERIMENT_RES = {
    "bare_como_curated_ground": _BARE_COMO_RE,
    "bare_como_curated_ground_v2": _BARE_COMO_RE,
    "colloquial_que_nem_feito": _COLLOQUIAL_RE,
    "broader_ground_window_como_article": _COMO_ARTICLE_WINDOW_RE,
}

_SPARK_PREFILTER_RES = {
    "bare_como_curated_ground": rf"\b(?:{_QUALITY_WORD})\s+como\s+(?!(?:um|uma|uns|umas)\b)",
    "bare_como_curated_ground_v2": rf"\b(?:{_QUALITY_WORD})\s+como\s+(?!(?:um|uma|uns|umas)\b)",
    "colloquial_que_nem_feito": rf"\b(?:{_GROUND_WORD})\s+(?:que\s+nem|feito|feita|feitos|feitas)\b",
    "broader_ground_window_como_article": (
        rf"\b(?:(?:tão|tao|mais|menos|muito|bem|quase|bastante)\s+)?"
        rf"(?:{_GROUND_WORD})\s+como\s+(?:um|uma|uns|umas)\b"
    ),
}

_STOP_TAIL_TOKENS = frozenset(
    {
        "e",
        "ou",
        "mas",
        "que",
        "quando",
        "porque",
        "pois",
        "se",
        "eu",
        "tu",
        "ele",
        "ela",
        "nós",
        "nos",
        "vocês",
        "eles",
        "elas",
        "me",
        "te",
        "lhe",
        "lhes",
        "é",
        "era",
        "foi",
        "será",
        "está",
        "estava",
        "tem",
        "tinha",
        "vai",
        "pode",
        "posso",
        "funciona",
        "será",
        "sempre",
        "também",
        "nunca",
    }
)
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
        "um",
        "uma",
        "uns",
        "umas",
        "todo",
        "toda",
        "todos",
        "todas",
        "meu",
        "minha",
        "meus",
        "minhas",
        "nosso",
        "nossa",
        "nossos",
        "nossas",
        "seu",
        "sua",
        "seus",
        "suas",
        "este",
        "esta",
        "estes",
        "estas",
        "esse",
        "essa",
        "esses",
        "essas",
        "isso",
        "isto",
        "aquele",
        "aquela",
        "aqueles",
        "aquelas",
        "se",
        "eu",
        "tu",
        "ele",
        "ela",
        "eles",
        "elas",
        "você",
        "voce",
        "vocês",
        "voces",
        "me",
        "te",
        "lhe",
        "lhes",
        "é",
        "era",
        "foi",
        "será",
        "está",
        "estava",
        "tem",
        "tinha",
        "vai",
        "pode",
        "posso",
        "funciona",
        "foi",
        "fosse",
        "foram",
        "eram",
        "são",
        "ser",
        "há",
        "ja",
        "já",
        "agora",
        "antes",
        "depois",
        "quando",
        "como",
        "com",
        "para",
        "por",
        "mais",
        "menos",
        "demais",
        "muitos",
        "muitas",
        "outros",
        "outras",
        "sempre",
        "também",
        "nunca",
        "só",
    }
)
_DEFINITE_ARTICLES = frozenset({"o", "a", "os", "as"})
_BARE_COMO_V2_ARTICLE_REJECT_HEADS = frozenset(
    {
        "que",
        "qual",
        "quais",
        "mesmo",
        "mesma",
        "mesmos",
        "mesmas",
        "já",
        "ja",
        "próprio",
        "proprio",
        "própria",
        "propria",
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
        "sistema",
        "profissional",
        "adulto",
    }
)
_COMPLEMENT_PREPOSITIONS = frozenset({"de", "do", "da"})
_NOISE_RE = re.compile(r"https?://|www\.|[@#]|\d+%|^\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class VehicleCandidate:
    raw: str
    clean: str
    head: str
    tail: str
    tokens: tuple[str, ...]
    start: int
    end: int
    label: str
    reason: str
    needs_review: bool


def experiment_dataset_path(experiment_slug: str) -> Path:
    """Return the organized Parquet path for one experiment's candidate dataset."""

    _validate_experiment_slug(experiment_slug)
    return EXPERIMENT_DATASET_ROOT / experiment_slug / "candidates"


def experiment_output_path(experiment_slug: str) -> Path:
    """Return the organized CSV/notes output path for one experiment."""

    _validate_experiment_slug(experiment_slug)
    return EXPERIMENT_OUTPUT_ROOT / experiment_slug


def prefilter_dataset_expansion_bronze_dataframe(bronze_df: Any, experiment_slug: str) -> Any:
    """Return bronze rows that can possibly match a spec-0007 experiment."""

    from pyspark.sql.functions import col

    _validate_experiment_slug(experiment_slug)
    return bronze_df.where(col("match_text").rlike(_SPARK_PREFILTER_RES[experiment_slug]))


def extract_dataset_expansion_rows(
    source_file: str,
    original_line_id: int,
    segment_id: int,
    text_normalized: str,
    match_text: str | None,
    experiment_slug: str,
) -> list[dict[str, object]]:
    """Extract reviewable spec-0007 candidate rows from one bronze segment."""

    _validate_experiment_slug(experiment_slug)
    searchable = match_text if match_text is not None else text_normalized.lower()
    pattern = _EXPERIMENT_RES[experiment_slug]
    rows: list[dict[str, object]] = []

    for match in pattern.finditer(searchable):
        ground_text = text_normalized[match.start("ground") : match.end("ground")]
        connector_text = text_normalized[match.start("connector") : match.end("connector")]
        text_before = text_normalized[: match.start("ground")].rstrip()[-LEFT_CONTEXT_CHARS:].lstrip()
        vehicle = _extract_experiment_vehicle(text_normalized, match.end("connector"), experiment_slug)
        if not vehicle.tokens:
            continue

        matched_text = text_normalized[match.start("ground") : match.end("connector")]
        char_end = vehicle.end
        rows.append(
            {
                "candidate_id": _candidate_id(
                    source_file,
                    original_line_id,
                    segment_id,
                    match.start("ground"),
                    char_end,
                    experiment_slug,
                ),
                "pattern_type": experiment_slug,
                "source_file": source_file,
                "original_line_id": original_line_id,
                "segment_id": segment_id,
                "connector_text": connector_text,
                "matched_text": matched_text,
                "candidate_full_text": _compact_text(text_before, matched_text, vehicle.clean),
                "text_before": text_before,
                "ground_text": ground_text,
                "ground_lemma": _GROUND_FORMS[ground_text.lower()],
                "ground_source": _ground_source(ground_text),
                "vehicle_text_raw": vehicle.raw,
                "vehicle_text_clean": vehicle.clean,
                "vehicle_head_clean": vehicle.head,
                "vehicle_tail_text": vehicle.tail,
                "quality_label": vehicle.label,
                "quality_reason": vehicle.reason,
                "needs_review": vehicle.needs_review,
                "char_start": match.start("ground"),
                "char_end": char_end,
            }
        )

    return sorted(rows, key=lambda row: (row["char_start"], row["char_end"], row["candidate_id"]))


def prepare_dataset_expansion_dataframe(bronze_df: Any, experiment_slug: str) -> Any:
    """Create a Spark candidate DataFrame for one spec-0007 experiment."""

    from pyspark.sql.functions import col, explode, lit, udf
    from pyspark.sql.types import ArrayType, BooleanType, IntegerType, LongType, StringType, StructField, StructType

    _validate_experiment_slug(experiment_slug)
    schema = ArrayType(
        StructType(
            [
                StructField("candidate_id", StringType(), nullable=False),
                StructField("pattern_type", StringType(), nullable=False),
                StructField("source_file", StringType(), nullable=False),
                StructField("original_line_id", LongType(), nullable=False),
                StructField("segment_id", IntegerType(), nullable=False),
                StructField("connector_text", StringType(), nullable=False),
                StructField("matched_text", StringType(), nullable=False),
                StructField("candidate_full_text", StringType(), nullable=False),
                StructField("text_before", StringType(), nullable=False),
                StructField("ground_text", StringType(), nullable=False),
                StructField("ground_lemma", StringType(), nullable=False),
                StructField("ground_source", StringType(), nullable=False),
                StructField("vehicle_text_raw", StringType(), nullable=False),
                StructField("vehicle_text_clean", StringType(), nullable=False),
                StructField("vehicle_head_clean", StringType(), nullable=False),
                StructField("vehicle_tail_text", StringType(), nullable=False),
                StructField("quality_label", StringType(), nullable=False),
                StructField("quality_reason", StringType(), nullable=False),
                StructField("needs_review", BooleanType(), nullable=False),
                StructField("char_start", IntegerType(), nullable=False),
                StructField("char_end", IntegerType(), nullable=False),
            ]
        )
    )
    extract_rows = udf(extract_dataset_expansion_rows, schema)

    return bronze_df.withColumn(
        "candidate",
        explode(
            extract_rows(
                col("source_file"),
                col("original_line_id"),
                col("segment_id"),
                col("text_normalized"),
                col("match_text"),
                lit(experiment_slug),
            )
        ),
    ).select("candidate.*")


def write_dataset_expansion_artifacts(candidates_df: Any, experiment_slug: str, mode: str = "overwrite") -> None:
    """Write the organized Parquet dataset and required review artifacts."""

    output_path = experiment_output_path(experiment_slug)
    accepted_df = accepted_candidates_dataframe(candidates_df)
    candidates_df.write.mode(mode).parquet(str(experiment_dataset_path(experiment_slug)))
    _write_csv(candidate_counts_dataframe(candidates_df), output_path / "candidate_counts.csv", mode)
    _write_csv(ground_vehicle_counts_dataframe(accepted_df), output_path / "ground_vehicle_counts.csv", mode)
    _write_csv(vehicle_counts_dataframe(accepted_df), output_path / "vehicle_counts.csv", mode)
    _write_csv(review_sample_dataframe(candidates_df), output_path / "review_sample.csv", mode)
    _write_csv(accepted_review_sample_dataframe(candidates_df), output_path / "accepted_review_sample.csv", mode)
    _write_quality_notes(candidates_df, experiment_slug, output_path / "quality_notes.md")


def accepted_candidates_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return candidates_df.where(col("quality_label").isin("keep", "trimmed"))


def candidate_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return candidates_df.groupBy("pattern_type", "quality_label").count().orderBy("pattern_type", col("count").desc())


def ground_vehicle_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.groupBy("pattern_type", "ground_lemma", "vehicle_head_clean")
        .count()
        .orderBy(col("count").desc(), "pattern_type", "ground_lemma", "vehicle_head_clean")
    )


def vehicle_counts_dataframe(candidates_df: Any) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.groupBy("pattern_type", "vehicle_head_clean")
        .count()
        .orderBy(col("count").desc(), "pattern_type", "vehicle_head_clean")
    )


def review_sample_dataframe(candidates_df: Any, limit: int = 200) -> Any:
    from pyspark.sql.functions import col

    return (
        candidates_df.select(
            "candidate_id",
            "pattern_type",
            "ground_text",
            "ground_lemma",
            "connector_text",
            "vehicle_text_raw",
            "vehicle_text_clean",
            "vehicle_head_clean",
            "quality_label",
            "quality_reason",
            "needs_review",
            "candidate_full_text",
            "source_file",
            "original_line_id",
            "segment_id",
        )
        .orderBy(col("needs_review").desc(), "quality_label", "candidate_id")
        .limit(limit)
    )


def accepted_review_sample_dataframe(candidates_df: Any, limit: int = 200) -> Any:
    from pyspark.sql.functions import col, length

    return (
        accepted_candidates_dataframe(candidates_df)
        .select(
            "candidate_id",
            "pattern_type",
            "ground_text",
            "ground_lemma",
            "connector_text",
            "vehicle_text_raw",
            "vehicle_text_clean",
            "vehicle_head_clean",
            "quality_label",
            "quality_reason",
            "needs_review",
            "candidate_full_text",
            "source_file",
            "original_line_id",
            "segment_id",
        )
        .orderBy(
            col("quality_label").desc(),
            length(col("vehicle_text_clean")).desc(),
            "ground_lemma",
            "vehicle_head_clean",
            "candidate_id",
        )
        .limit(limit)
    )


def _extract_experiment_vehicle(text: str, start: int, experiment_slug: str) -> VehicleCandidate:
    right = text[start:]
    leading = len(right) - len(right.lstrip())
    phrase_start = start + leading
    trimmed = right.lstrip()
    boundary = _BOUNDARY_RE.search(trimmed)
    raw_phrase = trimmed[: boundary.start() if boundary else len(trimmed)]
    raw_tokens = tuple(_word_tokens(raw_phrase))
    if not raw_tokens:
        return VehicleCandidate("", "", "", "", (), phrase_start, phrase_start, "reject", "missing_vehicle", True)

    selected = _select_vehicle_tokens(raw_tokens)
    if not selected:
        selected = raw_tokens[:1]
    selected = selected[:MAX_EXPERIMENT_VEHICLE_TOKENS]

    last_match = None
    for index, token_match in enumerate(_WORD_RE.finditer(raw_phrase)):
        if index == len(selected) - 1:
            last_match = token_match
            break
    phrase_end = phrase_start + (last_match.end() if last_match else 0)

    raw = _compact_text(*raw_tokens)
    clean_tokens = _clean_vehicle_tokens(raw_tokens, selected, experiment_slug)
    clean = _compact_text(*clean_tokens)
    head = clean_tokens[0].lower() if clean_tokens else ""
    tail = _compact_text(*clean_tokens[1:])
    label, reason, needs_review = _quality_decision(raw_tokens, selected, clean_tokens, experiment_slug)
    return VehicleCandidate(raw, clean, head, tail, tuple(selected), phrase_start, phrase_end, label, reason, needs_review)


def _select_vehicle_tokens(tokens: tuple[str, ...]) -> tuple[str, ...]:
    selected: list[str] = []
    for token in tokens:
        normalized = token.lower()
        if selected and normalized in _STOP_TAIL_TOKENS:
            break
        selected.append(token)
        if len(selected) == 1:
            continue
        if len(selected) >= 3 and selected[-2].lower() not in _COMPLEMENT_PREPOSITIONS:
            break
        if len(selected) >= MAX_EXPERIMENT_VEHICLE_TOKENS:
            break
    return tuple(selected)


def _clean_vehicle_tokens(
    raw_tokens: tuple[str, ...],
    selected: tuple[str, ...],
    experiment_slug: str,
) -> tuple[str, ...]:
    if experiment_slug != "bare_como_curated_ground_v2":
        return selected
    if len(raw_tokens) >= 2 and raw_tokens[0].lower() in _DEFINITE_ARTICLES:
        shifted = raw_tokens[1 : 1 + MAX_EXPERIMENT_VEHICLE_TOKENS]
        return _select_vehicle_tokens(shifted) or shifted[:1]
    return selected


def _quality_decision(
    raw_tokens: tuple[str, ...],
    selected: tuple[str, ...],
    clean_tokens: tuple[str, ...],
    experiment_slug: str,
) -> tuple[str, str, bool]:
    if not clean_tokens:
        return "reject", "missing_vehicle", True
    raw_head = selected[0].lower()
    head = clean_tokens[0].lower()
    clean = _compact_text(*clean_tokens)
    if experiment_slug == "bare_como_curated_ground_v2" and raw_head in _DEFINITE_ARTICLES:
        if len(raw_tokens) < 2 or head in _BARE_COMO_V2_ARTICLE_REJECT_HEADS or head in _BAD_VEHICLE_STARTS:
            return "reject", "bad_definite_article_vehicle", True
        article_reason = "stripped_definite_article"
    else:
        article_reason = ""
    if not head[0].isalpha() or head in _BAD_VEHICLE_STARTS:
        return "reject", "bad_vehicle_start", True
    if head in _GENERIC_VEHICLE_HEADS:
        return "review", "generic_or_role_like_vehicle_head", True
    if _NOISE_RE.search(clean) or any(_NOISE_RE.search(token) for token in selected):
        return "reject", "vehicle_noise", True
    if len(raw_tokens) > len(selected):
        return "trimmed", "trimmed_clause_like_tail", False
    if len(selected) > 1 and all(token[:1].isupper() for token in selected if token):
        return "review", "capitalized_multi_token_vehicle", True
    if article_reason:
        return "keep", article_reason, False
    return "keep", "short_vehicle", False


def _ground_source(ground_text: str) -> str:
    lemma = _GROUND_FORMS[ground_text.lower()]
    if lemma in _QUALITY_LEMMAS:
        return "curated_quality_list"
    return "curated_verb_list"


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


def _write_quality_notes(candidates_df: Any, experiment_slug: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    accepted_df = accepted_candidates_dataframe(candidates_df)
    counts = {row["quality_label"]: row["count"] for row in candidate_counts_dataframe(candidates_df).collect()}
    total = sum(counts.values())
    keepish = counts.get("keep", 0) + counts.get("trimmed", 0)
    keepish_rate = keepish / total if total else 0.0
    top_rows = ground_vehicle_counts_dataframe(accepted_df).limit(30).collect()

    lines = [
        f"# {experiment_slug} Quality Notes",
        "",
        "Generated by `notebooks/02_dataset_expansion_experiments_one_shard.ipynb`.",
        "",
        f"- Candidate rows: {total}",
        f"- Keep or trimmed rows: {keepish} ({keepish_rate:.1%})",
        f"- Quality-label counts: {counts}",
        "",
        "## Top Accepted Ground/Vehicle Pairs",
        "",
        "| ground_lemma | vehicle_head_clean | count |",
        "| --- | --- | ---: |",
    ]
    for row in top_rows:
        lines.append(f"| {row['ground_lemma']} | {row['vehicle_head_clean']} | {row['count']} |")
    lines.extend(
        [
            "",
            "## Review Prompt",
            "",
            "Inspect `review_sample.csv` for the dominant false-positive family before promoting this pattern.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_experiment_slug(experiment_slug: str) -> None:
    if experiment_slug not in EXPERIMENT_SLUGS:
        raise ValueError(f"Unknown spec-0007 experiment slug: {experiment_slug}")
