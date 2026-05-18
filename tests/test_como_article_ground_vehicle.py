import unittest
from types import ModuleType
from unittest.mock import patch

from tal_qual.como_article_ground_vehicle import (
    COMO_ARTICLE_BACKEND_EXPORT_DIR,
    COMO_ARTICLE_EXAMPLES_OUTPUT_PATH,
    COMO_ARTICLE_GROUND_COUNTS_OUTPUT_PATH,
    COMO_ARTICLE_GROUND_VEHICLE_COUNTS_OUTPUT_PATH,
    COMO_ARTICLE_GROUND_VEHICLE_OUTPUT_PATH,
    COMO_ARTICLE_REVIEW_SAMPLE_OUTPUT_PATH,
    COMO_ARTICLE_VEHICLE_COUNTS_OUTPUT_PATH,
    COMO_ARTICLE_VEHICLE_GROUND_COUNTS_OUTPUT_PATH,
    cleanup_como_article_backend_candidate,
    extract_como_article_ground_vehicle_rows,
    prefilter_como_article_ground_vehicle_bronze_dataframe,
    write_como_article_backend_export,
    write_como_article_csv_outputs,
)


class ComoArticleGroundVehicleTest(unittest.TestCase):
    def test_output_paths_match_spec_0006_contract(self):
        self.assertEqual("data/gold/como_article_ground_vehicle_candidates", str(COMO_ARTICLE_GROUND_VEHICLE_OUTPUT_PATH))
        self.assertEqual("outputs/como_article_ground_vehicle_counts.csv", str(COMO_ARTICLE_GROUND_VEHICLE_COUNTS_OUTPUT_PATH))
        self.assertEqual("outputs/como_article_vehicle_ground_counts.csv", str(COMO_ARTICLE_VEHICLE_GROUND_COUNTS_OUTPUT_PATH))
        self.assertEqual("outputs/como_article_ground_counts.csv", str(COMO_ARTICLE_GROUND_COUNTS_OUTPUT_PATH))
        self.assertEqual("outputs/como_article_vehicle_counts.csv", str(COMO_ARTICLE_VEHICLE_COUNTS_OUTPUT_PATH))
        self.assertEqual("outputs/como_article_examples.csv", str(COMO_ARTICLE_EXAMPLES_OUTPUT_PATH))
        self.assertEqual("outputs/como_article_review_sample.csv", str(COMO_ARTICLE_REVIEW_SAMPLE_OUTPUT_PATH))
        self.assertEqual("data/export/backend/comparisons/v1", str(COMO_ARTICLE_BACKEND_EXPORT_DIR))

    def test_extracts_curated_quality_ground_and_vehicle_phrase(self):
        rows = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "Sentia-se forte como um touro.")

        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("como_article_ground_vehicle", row["pattern_type"])
        self.assertEqual("como um", row["connector"])
        self.assertEqual("como um", row["connector_text"])
        self.assertEqual("forte como um", row["matched_text"])
        self.assertEqual("Sentia-se forte como um touro", row["candidate_full_text"])
        self.assertEqual("Sentia-se", row["tenor_text"])
        self.assertEqual("forte", row["ground_text"])
        self.assertEqual("forte", row["ground_lemma"])
        self.assertEqual("quality_adjective", row["ground_type"])
        self.assertEqual("curated_quality_list", row["ground_source"])
        self.assertEqual("touro", row["vehicle_text"])
        self.assertEqual("touro", row["vehicle_head"])
        self.assertEqual(1, row["vehicle_phrase_length_tokens"])
        self.assertEqual("keep", row["filter_label"])
        self.assertEqual("", row["reject_reason"])
        self.assertGreater(row["vehicle_start"], row["connector_end"])
        self.assertEqual(row["char_end"], row["vehicle_end"])

    def test_extracts_gender_variant_and_compact_vehicle_phrase(self):
        rows = extract_como_article_ground_vehicle_rows(
            "sample.txt",
            1,
            0,
            "O programa saiu leve como uma pluma no ar.",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("leve", rows[0]["ground_lemma"])
        self.assertEqual("pluma no ar", rows[0]["vehicle_text"])
        self.assertEqual("pluma", rows[0]["vehicle_head_lemma"])

    def test_extracts_curated_salient_verb_ground(self):
        rows = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "A decisão caiu como uma luva.")

        self.assertEqual(1, len(rows))
        self.assertEqual("caiu", rows[0]["ground_text"])
        self.assertEqual("cair", rows[0]["ground_lemma"])
        self.assertEqual("salient_verb", rows[0]["ground_type"])
        self.assertEqual("curated_verb_list", rows[0]["ground_source"])
        self.assertEqual("luva", rows[0]["vehicle_head_lemma"])

    def test_excludes_non_spec_connectors_and_uncurated_grounds(self):
        bare_como = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "O quarto estava frio como gelo.")
        que_nem = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "Ele trabalha que nem um robô.")
        uncurated = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "Ele ficou falso como uma moeda.")

        self.assertEqual([], bare_como)
        self.assertEqual([], que_nem)
        self.assertEqual([], uncurated)

    def test_rejects_generic_role_noise_and_overlong_vehicle(self):
        generic = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "O debate ficou grande como um tema nacional.")
        role = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "O termo foi conhecido forte como um sinal.")
        overlong = extract_como_article_ground_vehicle_rows(
            "sample.txt",
            1,
            0,
            "Ele ficou frio como uma pedra muito antiga no fundo do rio.",
        )

        self.assertEqual([], generic)
        self.assertEqual([], role)
        self.assertEqual([], overlong)

    def test_write_csv_outputs_wires_all_spec_summaries(self):
        writes = []

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
                writes.append((self.name, path, self.mode_value, self.option_value))

        class FakeDataFrame:
            def __init__(self, name):
                self.name = name
                self.write = FakeWriter(name)

            def coalesce(self, partitions):
                self.partitions = partitions
                return self

        with (
            patch(
                "tal_qual.como_article_ground_vehicle.como_article_ground_vehicle_counts_dataframe",
                return_value=FakeDataFrame("ground_vehicle"),
            ),
            patch(
                "tal_qual.como_article_ground_vehicle.como_article_vehicle_ground_counts_dataframe",
                return_value=FakeDataFrame("vehicle_ground"),
            ),
            patch(
                "tal_qual.como_article_ground_vehicle.como_article_ground_counts_dataframe",
                return_value=FakeDataFrame("ground"),
            ),
            patch(
                "tal_qual.como_article_ground_vehicle.como_article_vehicle_counts_dataframe",
                return_value=FakeDataFrame("vehicle"),
            ),
            patch(
                "tal_qual.como_article_ground_vehicle.como_article_examples_dataframe",
                return_value=FakeDataFrame("examples"),
            ),
            patch(
                "tal_qual.como_article_ground_vehicle.como_article_review_sample_dataframe",
                return_value=FakeDataFrame("review"),
            ),
        ):
            write_como_article_csv_outputs(FakeDataFrame("candidates"))

        self.assertEqual(
            [
                ("ground_vehicle", "outputs/como_article_ground_vehicle_counts.csv", "overwrite", ("header", True)),
                ("vehicle_ground", "outputs/como_article_vehicle_ground_counts.csv", "overwrite", ("header", True)),
                ("ground", "outputs/como_article_ground_counts.csv", "overwrite", ("header", True)),
                ("vehicle", "outputs/como_article_vehicle_counts.csv", "overwrite", ("header", True)),
                ("examples", "outputs/como_article_examples.csv", "overwrite", ("header", True)),
                ("review", "outputs/como_article_review_sample.csv", "overwrite", ("header", True)),
            ],
            writes,
        )

    def test_prefilter_uses_native_match_text_rlike(self):
        class FakeColumn:
            def __init__(self, name):
                self.name = name
                self.pattern = None

            def rlike(self, pattern):
                self.pattern = pattern
                return ("rlike", self.name, pattern)

        class FakeDataFrame:
            def __init__(self):
                self.condition = None

            def where(self, condition):
                self.condition = condition
                return self

        fake_column = FakeColumn("match_text")
        fake_df = FakeDataFrame()

        pyspark_module = ModuleType("pyspark")
        sql_module = ModuleType("pyspark.sql")
        functions_module = ModuleType("pyspark.sql.functions")
        functions_module.col = lambda name: fake_column

        with patch.dict(
            "sys.modules",
            {
                "pyspark": pyspark_module,
                "pyspark.sql": sql_module,
                "pyspark.sql.functions": functions_module,
            },
        ):
            result = prefilter_como_article_ground_vehicle_bronze_dataframe(fake_df)

        self.assertIs(fake_df, result)
        self.assertEqual(("rlike", "match_text", fake_column.pattern), fake_df.condition)
        self.assertIn("como\\s+(?:um|uma|uns|umas)", fake_column.pattern)
        self.assertIn("forte", fake_column.pattern)
        self.assertIn("trabalha", fake_column.pattern)

    def test_backend_cleanup_preserves_raw_and_trims_common_head_tail(self):
        row = extract_como_article_ground_vehicle_rows(
            "sample.txt",
            1,
            0,
            "O programa saiu leve como uma pluma no ar.",
        )[0]

        cleaned = cleanup_como_article_backend_candidate(row)

        self.assertEqual("v1", cleaned["dataset_version"])
        self.assertEqual("pluma no ar", cleaned["vehicle_text_raw"])
        self.assertEqual("pluma", cleaned["vehicle_text_clean"])
        self.assertEqual("no ar", cleaned["vehicle_tail_text"])
        self.assertEqual("trimmed_common_head_tail", cleaned["vehicle_cleaning_rule"])
        self.assertEqual("pluma", cleaned["vehicle_head_clean_lemma"])
        self.assertEqual("trimmed", cleaned["quality_label"])
        self.assertTrue(cleaned["visualization_ready"])

    def test_backend_cleanup_marks_role_like_rows_for_review(self):
        row = extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "Sentia-se forte como um touro.")[0]
        row["text_before"] = "usado"
        row["candidate_full_text"] = "usado forte como um touro"

        cleaned = cleanup_como_article_backend_candidate(row)

        self.assertEqual("review", cleaned["quality_label"])
        self.assertIn("role_or_classification_context", cleaned["quality_reason"])
        self.assertFalse(cleaned["visualization_ready"])
        self.assertTrue(cleaned["needs_review"])

    def test_write_backend_export_writes_contract_files_and_clean_aggregates(self):
        import json
        import tempfile
        from pathlib import Path

        rows = [
            extract_como_article_ground_vehicle_rows("sample.txt", 1, 0, "A decisão caiu como uma luva para todos.")[0],
            extract_como_article_ground_vehicle_rows("sample.txt", 2, 0, "A decisão caiu como uma luva.")[0],
            extract_como_article_ground_vehicle_rows("sample.txt", 3, 0, "Sentia-se forte como um touro.")[0],
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = write_como_article_backend_export(rows, tmpdir, generated_at="2026-05-17T00:00:00+00:00")
            export_dir = Path(tmpdir)

            self.assertEqual(3, manifest["candidate_count"])
            self.assertEqual(2, manifest["ground_count"])
            self.assertEqual(2, manifest["vehicle_count"])
            self.assertEqual(2, manifest["ground_vehicle_pair_count"])

            expected_files = {
                "candidates.jsonl",
                "ground_vehicle_counts.json",
                "vehicle_ground_counts.json",
                "ground_counts.json",
                "vehicle_counts.json",
                "examples.jsonl",
                "manifest.json",
                "review_sample.jsonl",
                "rejected_or_review_candidates.jsonl",
            }
            self.assertEqual(expected_files, {path.name for path in export_dir.iterdir()})

            ground_vehicle_counts = json.loads((export_dir / "ground_vehicle_counts.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "ground_lemma": "cair",
                    "vehicle_head_clean_lemma": "luva",
                    "count": 2,
                    "example_candidate_ids": [rows[0]["candidate_id"], rows[1]["candidate_id"]],
                },
                ground_vehicle_counts[0],
            )

            first_candidate = json.loads((export_dir / "candidates.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual("luva para todos", first_candidate["vehicle_text_raw"])
            self.assertEqual("luva", first_candidate["vehicle_text_clean"])
            self.assertEqual("luva", first_candidate["vehicle_head_clean_lemma"])


if __name__ == "__main__":
    unittest.main()
