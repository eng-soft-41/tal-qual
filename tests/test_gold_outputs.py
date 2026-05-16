import unittest
from unittest.mock import patch

from tal_qual.silver import (
    CANDIDATE_SAMPLE_OUTPUT_PATH,
    CONNECTOR_FAMILY_COUNTS_OUTPUT_PATH,
    PATTERN_TYPE_COUNTS_OUTPUT_PATH,
    SAMPLE_EXAMPLES_OUTPUT_PATH,
    SILVER_OUTPUT_PATH,
    TOP_VEHICLES_BY_FAMILY_OUTPUT_PATH,
    TOP_VEHICLES_BY_PATTERN_OUTPUT_PATH,
    TOP_VEHICLES_GLOBAL_OUTPUT_PATH,
    extract_candidate_rows,
    normalize_vehicle,
    write_gold_csv_outputs,
)


class GoldOutputTest(unittest.TestCase):
    def test_output_paths_match_expected_repo_layout(self):
        self.assertEqual("data/silver/comparison_candidates", str(SILVER_OUTPUT_PATH))
        self.assertEqual("outputs/candidates.csv", str(CANDIDATE_SAMPLE_OUTPUT_PATH))
        self.assertEqual("outputs/connector_family_counts.csv", str(CONNECTOR_FAMILY_COUNTS_OUTPUT_PATH))
        self.assertEqual("outputs/pattern_type_counts.csv", str(PATTERN_TYPE_COUNTS_OUTPUT_PATH))
        self.assertEqual("outputs/top_vehicles_global.csv", str(TOP_VEHICLES_GLOBAL_OUTPUT_PATH))
        self.assertEqual("outputs/top_vehicles_by_family.csv", str(TOP_VEHICLES_BY_FAMILY_OUTPUT_PATH))
        self.assertEqual("outputs/top_vehicles_by_pattern.csv", str(TOP_VEHICLES_BY_PATTERN_OUTPUT_PATH))
        self.assertEqual("outputs/sample_examples.csv", str(SAMPLE_EXAMPLES_OUTPUT_PATH))

    def test_vehicle_normalization_lowercases_cleans_whitespace_and_trims_punctuation(self):
        self.assertEqual("uma pedra antiga", normalize_vehicle("  , Uma   Pedra Antiga! "))

    def test_vehicle_normalization_preserves_leading_portuguese_articles(self):
        self.assertEqual("um raio", normalize_vehicle("Um RAIO"))
        self.assertEqual("uma sombra", normalize_vehicle(" uma sombra "))
        self.assertEqual("uns reis", normalize_vehicle("uns reis;"))
        self.assertEqual("umas folhas", normalize_vehicle("umas folhas."))

    def test_extracted_silver_rows_include_vehicle_normalized(self):
        rows = extract_candidate_rows(
            source_file="sample.txt",
            original_line_id=1,
            segment_id=0,
            text_normalized="Ele corre como um Raio Forte.",
        )

        self.assertEqual("Raio Forte", rows[0]["vehicle_raw"])
        self.assertEqual("raio forte", rows[0]["vehicle_normalized"])

    def test_gold_writer_emits_all_expected_csv_outputs(self):
        written_paths = []

        class FakeWriter:
            def __init__(self, name):
                self.name = name

            def mode(self, mode):
                self.mode_value = mode
                return self

            def option(self, key, value):
                self.option_value = (key, value)
                return self

            def csv(self, path):
                written_paths.append((self.name, path, self.mode_value, self.option_value))

        class FakeDataFrame:
            def __init__(self, name="silver"):
                self.name = name
                self.write = FakeWriter(name)

        with (
            patch("tal_qual.silver.candidate_sample_dataframe", return_value=FakeDataFrame("candidate_sample")),
            patch(
                "tal_qual.silver.connector_family_counts_dataframe",
                return_value=FakeDataFrame("connector_family_counts"),
            ),
            patch("tal_qual.silver.pattern_type_counts_dataframe", return_value=FakeDataFrame("pattern_type_counts")),
            patch("tal_qual.silver.top_vehicles_global_dataframe", return_value=FakeDataFrame("vehicle_normalized_top")),
            patch(
                "tal_qual.silver.top_vehicles_by_family_dataframe",
                return_value=FakeDataFrame("connector_family_vehicle_normalized_top"),
            ),
            patch(
                "tal_qual.silver.top_vehicles_by_pattern_dataframe",
                return_value=FakeDataFrame("pattern_type_vehicle_normalized_top"),
            ),
            patch("tal_qual.silver.sample_examples_dataframe", return_value=FakeDataFrame("sample_examples")),
        ):
            write_gold_csv_outputs(FakeDataFrame())

        self.assertEqual(
            [
                ("candidate_sample", "outputs/candidates.csv", "overwrite", ("header", True)),
                ("connector_family_counts", "outputs/connector_family_counts.csv", "overwrite", ("header", True)),
                ("pattern_type_counts", "outputs/pattern_type_counts.csv", "overwrite", ("header", True)),
                ("vehicle_normalized_top", "outputs/top_vehicles_global.csv", "overwrite", ("header", True)),
                (
                    "connector_family_vehicle_normalized_top",
                    "outputs/top_vehicles_by_family.csv",
                    "overwrite",
                    ("header", True),
                ),
                (
                    "pattern_type_vehicle_normalized_top",
                    "outputs/top_vehicles_by_pattern.csv",
                    "overwrite",
                    ("header", True),
                ),
                ("sample_examples", "outputs/sample_examples.csv", "overwrite", ("header", True)),
            ],
            written_paths,
        )


if __name__ == "__main__":
    unittest.main()
