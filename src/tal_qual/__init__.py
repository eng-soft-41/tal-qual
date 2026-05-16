"""Reusable helpers for the Portuguese simile candidate MVP."""

from tal_qual.bronze import (
    BRONZE_OUTPUT_PATH,
    RAW_CORPUS_GLOB,
    RAW_CORPUS_INPUT,
    prepare_bronze_dataframe,
    write_bronze_parquet,
)
from tal_qual.silver import extract_candidate_rows, prepare_silver_dataframe
from tal_qual.smoke import SAMPLE_TEXT_PATH, load_sample_text

__all__ = [
    "BRONZE_OUTPUT_PATH",
    "RAW_CORPUS_GLOB",
    "RAW_CORPUS_INPUT",
    "SAMPLE_TEXT_PATH",
    "extract_candidate_rows",
    "load_sample_text",
    "prepare_bronze_dataframe",
    "prepare_silver_dataframe",
    "write_bronze_parquet",
]
