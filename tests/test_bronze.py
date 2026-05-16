import unittest

from tal_qual.bronze import (
    BRONZE_OUTPUT_PATH,
    RAW_CORPUS_GLOB,
    RAW_CORPUS_INPUT,
    prepare_bronze_rows,
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


if __name__ == "__main__":
    unittest.main()
