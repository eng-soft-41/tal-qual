"""Reusable helpers for the Portuguese simile candidate MVP."""

from tal_qual.bronze import (
    BRONZE_OUTPUT_PATH,
    RAW_CORPUS_GLOB,
    RAW_CORPUS_INPUT,
    prepare_bronze_dataframe,
    write_bronze_parquet,
)
from tal_qual.silver import (
    SILVER_OUTPUT_PATH,
    connector_family_counts_dataframe,
    extract_candidate_rows,
    normalize_vehicle,
    pattern_type_counts_dataframe,
    prepare_silver_dataframe,
    sample_examples_dataframe,
    top_vehicles_by_family_dataframe,
    top_vehicles_by_pattern_dataframe,
    top_vehicles_global_dataframe,
    write_gold_csv_outputs,
    write_mvp_outputs,
    write_silver_parquet,
)
from tal_qual.smoke import SAMPLE_TEXT_PATH, load_sample_text

__all__ = [
    "BRONZE_OUTPUT_PATH",
    "RAW_CORPUS_GLOB",
    "RAW_CORPUS_INPUT",
    "SAMPLE_TEXT_PATH",
    "SILVER_OUTPUT_PATH",
    "connector_family_counts_dataframe",
    "extract_candidate_rows",
    "load_sample_text",
    "normalize_vehicle",
    "pattern_type_counts_dataframe",
    "prepare_bronze_dataframe",
    "prepare_silver_dataframe",
    "sample_examples_dataframe",
    "top_vehicles_by_family_dataframe",
    "top_vehicles_by_pattern_dataframe",
    "top_vehicles_global_dataframe",
    "write_bronze_parquet",
    "write_gold_csv_outputs",
    "write_mvp_outputs",
    "write_silver_parquet",
]
