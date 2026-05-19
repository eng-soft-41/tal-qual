import unittest

from tal_qual.bronze import (
    BRONZE_OUTPUT_PATH,
    RAW_CORPUS_GLOB,
    RAW_CORPUS_INPUT,
    load_or_build_bronze_dataframe,
    prepare_bronze_rows,
    repartition_raw_corpus_dataframe,
)


class BronzePreparationTest(unittest.TestCase):
    def test_paths_match_expected_repo_layout(self):
        self.assertEqual("data/raw/brwac-clean-1.txt.gz", str(RAW_CORPUS_INPUT))
        self.assertEqual("data/raw/*.txt.gz", str(RAW_CORPUS_GLOB))
        self.assertEqual("data/bronze/brwac_segments", str(BRONZE_OUTPUT_PATH))

    def test_prepare_bronze_rows_splits_end_boundaries_and_removes_empty_segments(self):
        rows = prepare_bronze_rows(
            source_file="data/raw/brwac-clean-1.txt.gz",
            original_line_id=7,
            raw_text="  Primeiro   trecho <END>   <END> Segundo trecho  ",
        )

        self.assertEqual(2, len(rows))
        self.assertEqual("Primeiro trecho", rows[0]["text_normalized"])
        self.assertEqual("Segundo trecho", rows[1]["text_normalized"])
        self.assertEqual([0, 1], [row["segment_id"] for row in rows])

    def test_prepare_bronze_rows_preserves_original_text_and_lowercases_match_text(self):
        rows = prepare_bronze_rows(
            source_file="data/raw/brwac-clean-1.txt.gz",
            original_line_id=3,
            raw_text="  Água   FRIA como UMA Pedra  ",
        )

        self.assertEqual("Água   FRIA como UMA Pedra", rows[0]["text_original"])
        self.assertEqual("Água FRIA como UMA Pedra", rows[0]["text_normalized"])
        self.assertEqual("água fria como uma pedra", rows[0]["match_text"])
        self.assertEqual("data/raw/brwac-clean-1.txt.gz", rows[0]["source_file"])
        self.assertEqual(3, rows[0]["original_line_id"])

    def test_repartition_raw_corpus_dataframe_uses_default_parallelism(self):
        class FakeSparkContext:
            defaultParallelism = 4

        class FakeSpark:
            sparkContext = FakeSparkContext()

        class FakeDataFrame:
            repartition_partitions = None

            def repartition(self, partitions):
                self.repartition_partitions = partitions
                return self

        raw_df = FakeDataFrame()

        result = repartition_raw_corpus_dataframe(FakeSpark(), raw_df)

        self.assertIs(raw_df, result)
        self.assertEqual(4, raw_df.repartition_partitions)

    def test_load_or_build_bronze_reloads_after_write_to_cut_raw_lineage(self):
        calls = []

        class FakeReader:
            def parquet(self, path):
                calls.append(("read", path))
                return f"bronze:{path}"

        class FakeSpark:
            read = FakeReader()

        class MissingPath:
            def __init__(self, value):
                self.value = value

            def exists(self):
                return False

            def __fspath__(self):
                return self.value

            def __str__(self):
                return self.value

        with (
            unittest.mock.patch("tal_qual.bronze.prepare_bronze_dataframe", return_value="prepared") as prepare,
            unittest.mock.patch("tal_qual.bronze.write_bronze_parquet") as write,
        ):
            result = load_or_build_bronze_dataframe(FakeSpark(), "raw.txt.gz", MissingPath("bronze-out"))

        prepare.assert_called_once()
        written_path = write.call_args.args[1]
        self.assertEqual("bronze-out", str(written_path))
        self.assertEqual("bronze:bronze-out", result)
        self.assertEqual([("read", "bronze-out")], calls)


if __name__ == "__main__":
    unittest.main()
