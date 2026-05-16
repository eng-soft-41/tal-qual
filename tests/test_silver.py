import unittest

from tal_qual.silver import (
    extract_candidate_rows,
)


class SilverExtractionTest(unittest.TestCase):
    def test_extracts_one_row_per_connector_match(self):
        rows = extract_candidate_rows(
            source_file="sample.txt",
            original_line_id=10,
            segment_id=2,
            text_normalized="Ele corria como um raio e gritava que nem torcida.",
        )

        self.assertEqual(2, len(rows))
        self.assertEqual(["como_article", "que_nem_bare"], [row["pattern_type"] for row in rows])
        self.assertEqual(["como um", "que nem"], [row["matched_text"] for row in rows])

    def test_excludes_generic_como_without_article_or_se(self):
        rows = extract_candidate_rows(
            source_file="sample.txt",
            original_line_id=1,
            segment_id=0,
            text_normalized="Ele explicou como fazia tudo e depois saiu.",
        )

        self.assertEqual([], rows)

    def test_extracts_agreed_pattern_variants_and_metadata(self):
        text = (
            "Era como umas ondas, falou como se soubesse, ficou tal qual pedra, "
            "parecia uma sombra, parecia um vulto, feita uma ponte, feitos uns reis, "
            "igual ao pai, igual umas folhas, igualzinho à mãe e igualzinhas umas bonecas."
        )
        rows = extract_candidate_rows("sample.txt", 1, 0, text)

        observed = [
            (row["connector_family"], row["pattern_type"], row["comparison_form"], row["matched_text"])
            for row in rows
        ]

        self.assertEqual(
            [
                ("como", "como_article", "nominal", "como umas"),
                ("como", "como_se", "clausal", "como se"),
                ("tal_qual", "tal_qual_bare", "bare", "tal qual"),
                ("parecer", "parecer_article", "nominal", "parecia uma"),
                ("parecer", "parecer_article", "nominal", "parecia um"),
                ("feito", "feito_article", "nominal", "feita uma"),
                ("feito", "feito_article", "nominal", "feitos uns"),
                ("igual", "igual_preposition", "prepositional", "igual ao"),
                ("igual", "igual_article", "nominal", "igual umas"),
                ("igualzinho", "igualzinho_preposition", "prepositional", "igualzinho à"),
                ("igualzinho", "igualzinho_article", "nominal", "igualzinhas umas"),
            ],
            observed,
        )

    def test_vehicle_context_and_offsets_are_based_on_normalized_segment_text(self):
        text = "Muito antes do exemplo, ele chegou como uma tempestade, assustando todos."
        rows = extract_candidate_rows("sample.txt", 3, 4, text)

        self.assertEqual(1, len(rows))
        row = rows[0]
        start = text.index("como uma")
        end = start + len("como uma")

        self.assertEqual(start, row["char_start"])
        self.assertEqual(end, row["char_end"])
        self.assertEqual("como uma", text[row["char_start"] : row["char_end"]])
        self.assertEqual("tempestade", row["vehicle_raw"])
        self.assertEqual("Muito antes do exemplo, ele chegou", row["text_before"])
        self.assertEqual(
            "Muito antes do exemplo, ele chegou como uma tempestade",
            row["candidate_full_text"],
        )

    def test_right_context_stops_at_segment_boundary_punctuation_or_120_characters(self):
        punctuation_rows = extract_candidate_rows(
            "sample.txt",
            1,
            0,
            "Ele corre como um raio. Outro texto.",
        )
        boundary_rows = extract_candidate_rows(
            "sample.txt",
            1,
            0,
            "Ele corre como um raio <END> outro texto.",
        )
        long_vehicle = "x" * 130
        capped_rows = extract_candidate_rows(
            "sample.txt",
            1,
            0,
            f"Ele corre como um {long_vehicle}",
        )

        self.assertEqual("raio", punctuation_rows[0]["vehicle_raw"])
        self.assertEqual("raio", boundary_rows[0]["vehicle_raw"])
        self.assertEqual(120, len(capped_rows[0]["vehicle_raw"]))

    def test_text_before_is_capped_at_80_characters(self):
        left = "a" * 100
        rows = extract_candidate_rows("sample.txt", 1, 0, f"{left} como um raio")

        self.assertEqual("a" * 80, rows[0]["text_before"])

    def test_candidate_id_is_deterministic_from_provenance_offsets_pattern_and_match(self):
        first = extract_candidate_rows("sample.txt", 1, 0, "Ele corre como um raio")[0]
        second = extract_candidate_rows("sample.txt", 1, 0, "Ele corre como um raio")[0]
        different_offset = extract_candidate_rows("sample.txt", 1, 0, "Agora ele corre como um raio")[0]

        self.assertEqual(first["candidate_id"], second["candidate_id"])
        self.assertNotEqual(first["candidate_id"], different_offset["candidate_id"])


if __name__ == "__main__":
    unittest.main()
