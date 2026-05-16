"""Phase A NLP refinement dataset helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping

REFINED_CANDIDATES_NLP_OUTPUT_PATH = Path("data/gold/refined_candidates_nlp")
PHASE_A_SCOPE_COUNTS_OUTPUT_PATH = Path("outputs/phase_a_scope_counts.csv")
PHASE_A_QUALITY_BUCKET_COUNTS_OUTPUT_PATH = Path("outputs/phase_a_quality_bucket_counts.csv")
PHASE_A_TOP_CLEAN_COMMON_NOUN_HEADS_OUTPUT_PATH = Path("outputs/phase_a_top_clean_common_noun_heads.csv")
PHASE_A_TOP_CHARTABLE_VEHICLE_HEADS_OUTPUT_PATH = Path("outputs/phase_a_top_chartable_vehicle_heads.csv")
PHASE_A_TOP_VEHICLE_HEADS_BY_PATTERN_OUTPUT_PATH = Path("outputs/phase_a_top_vehicle_heads_by_pattern.csv")
PHASE_A_REFINEMENT_EXAMPLES_OUTPUT_PATH = Path("outputs/phase_a_refinement_examples.csv")

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
TARGET_REFINEMENT_SCOPES = frozenset({"primary_nominal_article", "primary_nominal_bare"})
NOUN_LIKE_POS = frozenset({"NOUN", "PROPN", "PRON", "NUM"})
MAX_CLEAN_VEHICLE_TOKENS = 5
_URL_OR_SYMBOL_RE = re.compile(r"https?://|www\.|[@#=<>]|[^\w\sÀ-ÖØ-öø-ÿ,.;:!?'-]", re.IGNORECASE)
_ROLE_OR_CLASSIFICATION_RE = re.compile(
    r"\b(?:"
    r"trabalh\w*|atu\w*|serv\w*|"
    r"conhecid\w*|chamad\w*|classificad\w*|definid\w*|"
    r"considerad\w*|identificad\w*"
    r")\b",
    re.IGNORECASE,
)
_WHITESPACE_RE = re.compile(r"\s+")


def nlp_refinement_scope(pattern_type: str) -> str:
    """Map a silver connector pattern to the Phase A refinement scope."""

    return SCOPE_BY_PATTERN_TYPE.get(pattern_type, OUT_OF_SCOPE)


def build_nlp_parse_text(matched_text: str, vehicle_raw: str) -> str:
    """Build the controlled parse window from connector text and raw vehicle."""

    return _compact_text(matched_text, vehicle_raw)


def refine_candidate_row(row: Mapping[str, Any], parser: Any | None = None) -> dict[str, Any]:
    """Carry one silver row forward into the minimal refined dataset shape."""

    refined = {field: row[field] for field in SILVER_TRACEABILITY_FIELDS if field in row}
    refined["nlp_refinement_scope"] = nlp_refinement_scope(str(row.get("pattern_type", "")))
    refined["nlp_parse_text"] = build_nlp_parse_text(
        str(row.get("matched_text", "")),
        str(row.get("vehicle_raw", "")),
    )
    refined.update(_extract_vehicle_structure(refined, parser or load_portuguese_parser()))
    refined.update(_assess_vehicle_quality(refined))
    return refined


def refine_candidate_rows(rows: Iterable[Mapping[str, Any]], parser: Any | None = None) -> list[dict[str, Any]]:
    """Carry silver candidate rows forward without changing cardinality."""

    row_parser = parser or load_portuguese_parser()
    return [refine_candidate_row(row, row_parser) for row in rows]


def sample_debug_rows(
    rows: Iterable[Mapping[str, Any]],
    rows_per_pattern: int = 25,
    parser: Any | None = None,
) -> list[dict[str, Any]]:
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

    return refine_candidate_rows(sampled, parser)


def prepare_refined_dataframe(silver_df: Any) -> Any:
    """Create a Spark DataFrame for the minimal refined candidate dataset."""

    from pyspark.sql.functions import col, concat_ws, lit, regexp_replace, struct, trim, udf, when
    from pyspark.sql.types import (
        BooleanType,
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    scope_column = lit(OUT_OF_SCOPE)
    for pattern_type, scope in SCOPE_BY_PATTERN_TYPE.items():
        scope_column = when(col("pattern_type") == pattern_type, scope).otherwise(scope_column)

    parse_text_column = trim(regexp_replace(concat_ws(" ", col("matched_text"), col("vehicle_raw")), r"\s+", " "))

    vehicle_structure_schema = StructType(
        [
            StructField("vehicle_phrase_nlp", StringType(), nullable=False),
            StructField("vehicle_head", StringType(), nullable=False),
            StructField("vehicle_head_lemma", StringType(), nullable=False),
            StructField("vehicle_head_pos", StringType(), nullable=False),
            StructField("vehicle_phrase_length_tokens", IntegerType(), nullable=False),
            StructField("vehicle_extraction_confidence", StringType(), nullable=False),
            StructField("nlp_model_name", StringType(), nullable=False),
            StructField("nlp_model_version", StringType(), nullable=False),
            StructField("structural_quality_bucket", StringType(), nullable=False),
            StructField("vehicle_is_clean_common_noun", BooleanType(), nullable=False),
            StructField("vehicle_is_chartable_vehicle", BooleanType(), nullable=False),
            StructField("vehicle_reject_reason", StringType(), nullable=False),
        ]
    )
    extract_vehicle_structure = udf(_vehicle_structure_for_spark_row, vehicle_structure_schema)

    scoped_df = (
        silver_df.select(*SILVER_TRACEABILITY_FIELDS)
        .withColumn("nlp_refinement_scope", scope_column)
        .withColumn("nlp_parse_text", parse_text_column)
    )
    return (
        scoped_df.withColumn(
            "vehicle_structure",
            extract_vehicle_structure(struct(*[col(name) for name in scoped_df.columns])),
        )
        .select("*", "vehicle_structure.*")
        .drop("vehicle_structure")
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


def refinement_scope_counts_dataframe(refined_df: Any) -> Any:
    """Count refined candidates by Phase A refinement scope."""

    from pyspark.sql.functions import col

    return refined_df.groupBy("nlp_refinement_scope").count().orderBy(
        col("count").desc(),
        col("nlp_refinement_scope"),
    )


def structural_quality_bucket_counts_dataframe(refined_df: Any) -> Any:
    """Count refined candidates by Structural Quality Bucket."""

    from pyspark.sql.functions import col

    return refined_df.groupBy("structural_quality_bucket").count().orderBy(
        col("count").desc(),
        col("structural_quality_bucket"),
    )


def top_clean_common_noun_vehicle_heads_dataframe(refined_df: Any) -> Any:
    """Count conservative clean common-noun vehicle heads by lemma."""

    return _top_refined_vehicle_heads_dataframe(refined_df, [], "vehicle_is_clean_common_noun")


def top_chartable_vehicle_heads_dataframe(refined_df: Any) -> Any:
    """Count broader chartable vehicle heads by lemma."""

    return _top_refined_vehicle_heads_dataframe(refined_df, [], "vehicle_is_chartable_vehicle")


def top_vehicle_heads_by_pattern_dataframe(refined_df: Any) -> Any:
    """Count chartable vehicle head lemmas by silver pattern type."""

    return _top_refined_vehicle_heads_dataframe(refined_df, ["pattern_type"], "vehicle_is_chartable_vehicle")


def refinement_examples_dataframe(refined_df: Any, examples_per_pattern_bucket: int = 10) -> Any:
    """Build deterministic side-by-side raw/refined vehicle examples."""

    from pyspark.sql import Window
    from pyspark.sql.functions import col, row_number

    if examples_per_pattern_bucket < 1:
        raise ValueError("examples_per_pattern_bucket must be at least 1")

    example_columns = [
        "candidate_id",
        "source_file",
        "original_line_id",
        "segment_id",
        "pattern_type",
        "nlp_refinement_scope",
        "structural_quality_bucket",
        "matched_text",
        "vehicle_raw",
        "vehicle_normalized",
        "vehicle_phrase_nlp",
        "vehicle_head",
        "vehicle_head_lemma",
        "vehicle_head_pos",
        "vehicle_is_clean_common_noun",
        "vehicle_is_chartable_vehicle",
        "vehicle_reject_reason",
        "candidate_full_text",
        "char_start",
        "char_end",
    ]
    dedupe_window = Window.partitionBy("pattern_type", "structural_quality_bucket", "candidate_full_text").orderBy(
        col("source_file"),
        col("original_line_id"),
        col("segment_id"),
        col("char_start"),
        col("candidate_id"),
    )
    example_window = Window.partitionBy("pattern_type", "structural_quality_bucket").orderBy(
        col("source_file"),
        col("original_line_id"),
        col("segment_id"),
        col("char_start"),
        col("candidate_id"),
    )

    return (
        refined_df.select(*example_columns)
        .withColumn("dedupe_rank", row_number().over(dedupe_window))
        .where(col("dedupe_rank") == 1)
        .drop("dedupe_rank")
        .withColumn("example_rank", row_number().over(example_window))
        .where(col("example_rank") <= examples_per_pattern_bucket)
        .orderBy("pattern_type", "structural_quality_bucket", "example_rank")
    )


def write_phase_a_csv_outputs(
    refined_df: Any,
    scope_counts_path: str | Path = PHASE_A_SCOPE_COUNTS_OUTPUT_PATH,
    quality_bucket_counts_path: str | Path = PHASE_A_QUALITY_BUCKET_COUNTS_OUTPUT_PATH,
    top_clean_common_noun_heads_path: str | Path = PHASE_A_TOP_CLEAN_COMMON_NOUN_HEADS_OUTPUT_PATH,
    top_chartable_vehicle_heads_path: str | Path = PHASE_A_TOP_CHARTABLE_VEHICLE_HEADS_OUTPUT_PATH,
    top_vehicle_heads_by_pattern_path: str | Path = PHASE_A_TOP_VEHICLE_HEADS_BY_PATTERN_OUTPUT_PATH,
    refinement_examples_path: str | Path = PHASE_A_REFINEMENT_EXAMPLES_OUTPUT_PATH,
    examples_per_pattern_bucket: int = 10,
    mode: str = "overwrite",
) -> None:
    """Write deterministic compact Phase A CSV outputs for inspection."""

    _write_csv(refinement_scope_counts_dataframe(refined_df), scope_counts_path, mode)
    _write_csv(structural_quality_bucket_counts_dataframe(refined_df), quality_bucket_counts_path, mode)
    _write_csv(top_clean_common_noun_vehicle_heads_dataframe(refined_df), top_clean_common_noun_heads_path, mode)
    _write_csv(top_chartable_vehicle_heads_dataframe(refined_df), top_chartable_vehicle_heads_path, mode)
    _write_csv(top_vehicle_heads_by_pattern_dataframe(refined_df), top_vehicle_heads_by_pattern_path, mode)
    _write_csv(refinement_examples_dataframe(refined_df, examples_per_pattern_bucket), refinement_examples_path, mode)


def summarize_refined_rows(
    rows: Iterable[Mapping[str, Any]],
    examples_per_pattern_bucket: int = 10,
) -> dict[str, list[dict[str, Any]]]:
    """Summarize tiny refined row samples with the same keys used by the Spark CSV outputs."""

    row_list = list(rows)
    return {
        "scope_counts": _count_rows(row_list, ["nlp_refinement_scope"]),
        "quality_bucket_counts": _count_rows(row_list, ["structural_quality_bucket"]),
        "top_clean_common_noun_heads": _top_refined_vehicle_head_rows(row_list, [], "vehicle_is_clean_common_noun"),
        "top_chartable_vehicle_heads": _top_refined_vehicle_head_rows(row_list, [], "vehicle_is_chartable_vehicle"),
        "top_vehicle_heads_by_pattern": _top_refined_vehicle_head_rows(
            row_list,
            ["pattern_type"],
            "vehicle_is_chartable_vehicle",
        ),
        "refinement_examples": _refinement_example_rows(row_list, examples_per_pattern_bucket),
    }


def load_portuguese_parser(model_name: str = "pt_core_news_sm") -> Any:
    """Load the default Portuguese spaCy parser, falling back to no extraction."""

    try:
        import spacy
    except ImportError:
        return _UnavailableParser()

    try:
        nlp = spacy.load(model_name)
    except OSError:
        return _UnavailableParser(model_name=model_name)

    return _SpacyParser(nlp)


def _extract_vehicle_structure(refined: Mapping[str, Any], parser: Any) -> dict[str, Any]:
    base = _empty_vehicle_structure(parser)
    if refined["nlp_refinement_scope"] not in TARGET_REFINEMENT_SCOPES:
        base["vehicle_extraction_confidence"] = "not_in_first_slice_scope"
        return base

    if isinstance(parser, _UnavailableParser) or bool(getattr(parser, "parser_unavailable", False)):
        base["vehicle_extraction_confidence"] = "parser_unavailable"
        return base

    doc = parser(str(refined.get("nlp_parse_text", "")))
    vehicle_start = len(str(refined.get("matched_text", "")).split())

    noun_chunk_result = _vehicle_from_noun_chunks(doc, vehicle_start)
    if noun_chunk_result is not None:
        return {**base, **noun_chunk_result}

    fallback_result = _vehicle_from_pos_fallback(doc, vehicle_start)
    if fallback_result is not None:
        return {**base, **fallback_result}

    base["vehicle_extraction_confidence"] = "no_noun_like_vehicle"
    return base


def _vehicle_from_noun_chunks(doc: Any, vehicle_start: int) -> dict[str, Any] | None:
    for chunk in getattr(doc, "noun_chunks", []):
        root = getattr(chunk, "root", None)
        if root is None:
            continue
        if int(getattr(root, "i", -1)) < vehicle_start:
            continue
        if str(getattr(root, "pos_", "")) not in NOUN_LIKE_POS:
            continue

        phrase_start = max(int(getattr(chunk, "start", vehicle_start)), vehicle_start)
        phrase_end = int(getattr(chunk, "end", phrase_start))
        phrase_tokens = _doc_tokens(doc)[phrase_start:phrase_end]
        phrase_text = _compact_text(*(str(getattr(token, "text", "")) for token in phrase_tokens))
        return _vehicle_result(
            phrase_text=phrase_text or str(getattr(chunk, "text", "")),
            head=root,
            phrase_length=len(phrase_tokens) or len(chunk),
            confidence="noun_chunk",
        )
    return None


def _vehicle_from_pos_fallback(doc: Any, vehicle_start: int) -> dict[str, Any] | None:
    tokens = _doc_tokens(doc)
    for index, token in enumerate(tokens[vehicle_start:], start=vehicle_start):
        if str(getattr(token, "pos_", "")) not in NOUN_LIKE_POS:
            continue

        phrase_tokens = [token]
        for following in tokens[index + 1 :]:
            if str(getattr(following, "pos_", "")) in {"ADJ", "NOUN", "PROPN"}:
                phrase_tokens.append(following)
                continue
            break

        return _vehicle_result(
            phrase_text=_compact_text(*(str(getattr(item, "text", "")) for item in phrase_tokens)),
            head=token,
            phrase_length=len(phrase_tokens),
            confidence="pos_fallback",
        )
    return None


def _vehicle_result(phrase_text: str, head: Any, phrase_length: int, confidence: str) -> dict[str, Any]:
    return {
        "vehicle_phrase_nlp": phrase_text,
        "vehicle_head": str(getattr(head, "text", "")),
        "vehicle_head_lemma": str(getattr(head, "lemma_", "")),
        "vehicle_head_pos": str(getattr(head, "pos_", "")),
        "vehicle_phrase_length_tokens": phrase_length,
        "vehicle_extraction_confidence": confidence,
    }


def _empty_vehicle_structure(parser: Any) -> dict[str, Any]:
    return {
        "vehicle_phrase_nlp": "",
        "vehicle_head": "",
        "vehicle_head_lemma": "",
        "vehicle_head_pos": "",
        "vehicle_phrase_length_tokens": 0,
        "vehicle_extraction_confidence": "",
        "nlp_model_name": str(getattr(parser, "model_name", "")),
        "nlp_model_version": str(getattr(parser, "model_version", "")),
    }


def _assess_vehicle_quality(refined: Mapping[str, Any]) -> dict[str, Any]:
    bucket = _structural_quality_bucket(refined)
    is_clean_common_noun = _is_clean_common_noun(refined, bucket)
    is_chartable = is_clean_common_noun or bucket == "proper_name_vehicle"

    return {
        "structural_quality_bucket": bucket,
        "vehicle_is_clean_common_noun": is_clean_common_noun,
        "vehicle_is_chartable_vehicle": is_chartable,
        "vehicle_reject_reason": "" if is_clean_common_noun else bucket,
    }


def _structural_quality_bucket(refined: Mapping[str, Any]) -> str:
    confidence = str(refined.get("vehicle_extraction_confidence", ""))
    vehicle_raw = str(refined.get("vehicle_raw", ""))
    phrase = str(refined.get("vehicle_phrase_nlp", ""))
    head = str(refined.get("vehicle_head", ""))
    head_pos = str(refined.get("vehicle_head_pos", ""))
    phrase_length = int(refined.get("vehicle_phrase_length_tokens", 0))

    if confidence == "not_in_first_slice_scope":
        return "not_in_first_slice_scope"
    if confidence == "parser_unavailable":
        return "parser_uncertain"
    if not vehicle_raw.strip():
        return "empty_vehicle"
    if _URL_OR_SYMBOL_RE.search(vehicle_raw) or _URL_OR_SYMBOL_RE.search(phrase):
        return "url_or_symbol_noise"
    if not head:
        return "clausal_or_verbal_continuation" if vehicle_raw.strip() else "empty_vehicle"
    if head_pos == "PRON":
        return "pronoun_vehicle"
    if head_pos == "NUM":
        return "numeric_vehicle"
    if phrase_length > MAX_CLEAN_VEHICLE_TOKENS:
        return "overly_long_vehicle_phrase"
    if _has_role_or_classification_risk(refined):
        return "role_or_classification_risk"
    if head_pos == "PROPN":
        return "proper_name_vehicle"
    if head_pos == "NOUN":
        return "clean_nominal_vehicle"
    return "parser_uncertain"


def _is_clean_common_noun(refined: Mapping[str, Any], bucket: str) -> bool:
    return (
        bucket == "clean_nominal_vehicle"
        and str(refined.get("vehicle_head_pos", "")) == "NOUN"
        and bool(str(refined.get("vehicle_head_lemma", "")).strip())
        and 0 < int(refined.get("vehicle_phrase_length_tokens", 0)) <= MAX_CLEAN_VEHICLE_TOKENS
    )


def _has_role_or_classification_risk(refined: Mapping[str, Any]) -> bool:
    context = _compact_text(
        str(refined.get("text_before", "")),
        str(refined.get("matched_text", "")),
        str(refined.get("vehicle_raw", "")),
    )
    return bool(_ROLE_OR_CLASSIFICATION_RE.search(context))


def _doc_tokens(doc: Any) -> list[Any]:
    return list(doc)


def _top_refined_vehicle_heads_dataframe(refined_df: Any, group_columns: list[str], eligibility_column: str) -> Any:
    from pyspark.sql.functions import col, count, countDistinct, min as spark_min

    grouped_columns = [*group_columns, "vehicle_head_lemma"]
    order_columns = [col("occurrence_count").desc(), *[col(column) for column in grouped_columns]]

    return (
        refined_df.where(col(eligibility_column))
        .where(col("vehicle_head_lemma") != "")
        .groupBy(*grouped_columns)
        .agg(
            count("*").alias("occurrence_count"),
            countDistinct("candidate_full_text").alias("distinct_candidate_text_count"),
            countDistinct("vehicle_phrase_nlp").alias("distinct_refined_phrase_count"),
            spark_min("vehicle_head").alias("representative_vehicle_head"),
            spark_min("vehicle_phrase_nlp").alias("representative_vehicle_phrase"),
        )
        .orderBy(*order_columns)
    )


def _write_csv(dataframe: Any, output_path: str | Path, mode: str) -> None:
    dataframe.write.mode(mode).option("header", True).csv(str(output_path))


def _count_rows(rows: list[Mapping[str, Any]], group_columns: list[str]) -> list[dict[str, Any]]:
    counts: dict[tuple[Any, ...], int] = {}
    for row in rows:
        key = tuple(row.get(column, "") for column in group_columns)
        counts[key] = counts.get(key, 0) + 1

    output = [
        {**{column: key[index] for index, column in enumerate(group_columns)}, "count": count}
        for key, count in counts.items()
    ]
    return sorted(output, key=lambda item: (-int(item["count"]), *[str(item[column]) for column in group_columns]))


def _top_refined_vehicle_head_rows(
    rows: list[Mapping[str, Any]],
    group_columns: list[str],
    eligibility_column: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for row in rows:
        if not bool(row.get(eligibility_column, False)):
            continue
        if not str(row.get("vehicle_head_lemma", "")).strip():
            continue
        key = tuple([*(row.get(column, "") for column in group_columns), row.get("vehicle_head_lemma", "")])
        groups.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    grouped_columns = [*group_columns, "vehicle_head_lemma"]
    for key, grouped_rows in groups.items():
        output.append(
            {
                **{column: key[index] for index, column in enumerate(grouped_columns)},
                "occurrence_count": len(grouped_rows),
                "distinct_candidate_text_count": len(
                    {str(row.get("candidate_full_text", "")) for row in grouped_rows}
                ),
                "distinct_refined_phrase_count": len({str(row.get("vehicle_phrase_nlp", "")) for row in grouped_rows}),
                "representative_vehicle_head": min(str(row.get("vehicle_head", "")) for row in grouped_rows),
                "representative_vehicle_phrase": min(str(row.get("vehicle_phrase_nlp", "")) for row in grouped_rows),
            }
        )

    return sorted(
        output,
        key=lambda item: (
            -int(item["occurrence_count"]),
            *[str(item[column]) for column in grouped_columns],
        ),
    )


def _refinement_example_rows(
    rows: list[Mapping[str, Any]],
    examples_per_pattern_bucket: int,
) -> list[dict[str, Any]]:
    if examples_per_pattern_bucket < 1:
        raise ValueError("examples_per_pattern_bucket must be at least 1")

    example_columns = [
        "candidate_id",
        "source_file",
        "original_line_id",
        "segment_id",
        "pattern_type",
        "nlp_refinement_scope",
        "structural_quality_bucket",
        "matched_text",
        "vehicle_raw",
        "vehicle_normalized",
        "vehicle_phrase_nlp",
        "vehicle_head",
        "vehicle_head_lemma",
        "vehicle_head_pos",
        "vehicle_is_clean_common_noun",
        "vehicle_is_chartable_vehicle",
        "vehicle_reject_reason",
        "candidate_full_text",
        "char_start",
        "char_end",
    ]
    ordered = sorted(rows, key=_refined_row_sort_key)
    seen: set[tuple[Any, ...]] = set()
    examples_by_group: dict[tuple[Any, ...], int] = {}
    examples: list[dict[str, Any]] = []

    for row in ordered:
        group = (row.get("pattern_type", ""), row.get("structural_quality_bucket", ""))
        dedupe_key = (*group, row.get("candidate_full_text", ""))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        rank = examples_by_group.get(group, 0) + 1
        if rank > examples_per_pattern_bucket:
            continue
        examples_by_group[group] = rank
        examples.append({**{column: row.get(column, "") for column in example_columns}, "example_rank": rank})

    return sorted(
        examples,
        key=lambda item: (
            str(item["pattern_type"]),
            str(item["structural_quality_bucket"]),
            int(item["example_rank"]),
        ),
    )


class _SpacyParser:
    def __init__(self, nlp: Any):
        self.nlp = nlp
        meta = getattr(nlp, "meta", {})
        self.model_name = str(meta.get("name", getattr(nlp, "lang", "spacy")))
        self.model_version = str(meta.get("version", ""))

    def __call__(self, text: str) -> Any:
        return self.nlp(text)


class _UnavailableParser:
    model_version = ""

    def __init__(self, model_name: str = ""):
        self.model_name = model_name

    def __call__(self, text: str) -> Any:
        return []


_SPARK_WORKER_PARSER: Any | None = None


def _vehicle_structure_for_spark_row(row: Any) -> dict[str, Any]:
    global _SPARK_WORKER_PARSER

    if _SPARK_WORKER_PARSER is None:
        _SPARK_WORKER_PARSER = load_portuguese_parser()

    row_dict = row.asDict() if hasattr(row, "asDict") else dict(row)
    refined = refine_candidate_row(row_dict, parser=_SPARK_WORKER_PARSER)
    return {
        "vehicle_phrase_nlp": str(refined["vehicle_phrase_nlp"]),
        "vehicle_head": str(refined["vehicle_head"]),
        "vehicle_head_lemma": str(refined["vehicle_head_lemma"]),
        "vehicle_head_pos": str(refined["vehicle_head_pos"]),
        "vehicle_phrase_length_tokens": int(refined["vehicle_phrase_length_tokens"]),
        "vehicle_extraction_confidence": str(refined["vehicle_extraction_confidence"]),
        "nlp_model_name": str(refined["nlp_model_name"]),
        "nlp_model_version": str(refined["nlp_model_version"]),
        "structural_quality_bucket": str(refined["structural_quality_bucket"]),
        "vehicle_is_clean_common_noun": bool(refined["vehicle_is_clean_common_noun"]),
        "vehicle_is_chartable_vehicle": bool(refined["vehicle_is_chartable_vehicle"]),
        "vehicle_reject_reason": str(refined["vehicle_reject_reason"]),
    }


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


def _refined_row_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(row.get("pattern_type", "")),
        str(row.get("structural_quality_bucket", "")),
        str(row.get("source_file", "")),
        int(row.get("original_line_id", 0)),
        int(row.get("segment_id", 0)),
        int(row.get("char_start", 0)),
        str(row.get("candidate_id", "")),
    )
