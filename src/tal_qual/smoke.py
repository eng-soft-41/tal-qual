"""Minimal Spark smoke-run helpers.

The first MVP slice only proves that the Dockerized PySpark notebook can import
project code and read a tiny Portuguese text sample through Spark.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SAMPLE_TEXT_PATH = Path("data/sample/portuguese-similes-smoke.txt")


def load_sample_text(spark: Any, repo_root: str | Path = ".") -> Any:
    """Read the tracked smoke sample as a Spark DataFrame.

    The Spark session is passed in by the notebook so importing this module does
    not require PySpark to be installed in non-Spark development environments.
    """

    sample_path = Path(repo_root) / SAMPLE_TEXT_PATH
    return spark.read.text(str(sample_path))
