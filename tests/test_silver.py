import unittest

from tal_qual.bronze import prepare_bronze_rows
from tal_qual.silver import (
    extract_candidate_rows,
)


class SilverExtractionTest(unittest.TestCase):
    def test_end_boundaries_are_extracted_as_separate_segments(self):
        bronze_rows = prepare_bronze_rows(
            source_file="sample.txt",
            original_line_id=7,
            raw_text="Antes como um raio sem fim <END> depois como uma sombra.",
        )
        rows = [
            candidate
            for bronze_row in bronze_rows
            for candidate in extract_candidate_rows(
                source_file=str(bronze_row["source_file"]),
                original_line_id=int(bronze_row["original_line_id"]),
                segment_id=int(bronze_row["segment_id"]),
                text_normalized=str(bronze_row["text_normalized"]),
                match_text=str(bronze_row["match_text"]),
            )
        ]

        self.assertEqual([0, 1], [row["segment_id"] for row in rows])
        self.assertEqual(["raio sem fim", "sombra"], [row["vehicle_raw"] for row in rows])
        self.assertTrue(all("<END>" not in row["candidate_full_text"] for row in rows))

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
            text_normalized="Ele explicou como fazia tudo, como o processo funciona e como pedra vira cal.",
        )

        self.assertEqual([], rows)

    def test_includes_only_agreed_narrow_como_variants(self):
        text = "como um raio, como uma sombra, como uns reis, como umas ondas, como se fosse noite"
        rows = extract_candidate_rows("sample.txt", 1, 0, text)

        self.assertEqual(
            ["como um", "como uma", "como uns", "como umas", "como se"],
            [row["matched_text"] for row in rows],
        )
        self.assertEqual(
            ["como_article", "como_article", "como_article", "como_article", "como_se"],
            [row["pattern_type"] for row in rows],
        )

    def test_extracts_agreed_pattern_variants_and_metadata(self):
        text = (
            "Parece um raio, parecia uma sombra, pareceu um vulto, ficou que nem pedra, "
            "ficou tal qual ponte, feito um rei, feita uma ponte, feitos uns reis, feitas umas folhas, "
            "igual a pai, igual ao pai, igual à mãe, igual aos tios, igual às tias, "
            "igual um raio, igual uma sombra, igual uns rios, igual umas folhas, "
            "igualzinho a pai, igualzinha ao pai, igualzinhos à mãe, igualzinhas aos tios, igualzinho às tias, "
            "igualzinho um raio, igualzinha uma sombra, igualzinhos uns rios, igualzinhas umas bonecas."
        )
        rows = extract_candidate_rows("sample.txt", 1, 0, text)

        observed = [
            (row["connector_family"], row["pattern_type"], row["comparison_form"], row["matched_text"])
            for row in rows
        ]

        self.assertEqual(
            [
                ("parecer", "parecer_article", "nominal", "Parece um"),
                ("parecer", "parecer_article", "nominal", "parecia uma"),
                ("parecer", "parecer_article", "nominal", "pareceu um"),
                ("que_nem", "que_nem_bare", "bare", "que nem"),
                ("tal_qual", "tal_qual_bare", "bare", "tal qual"),
                ("feito", "feito_article", "nominal", "feito um"),
                ("feito", "feito_article", "nominal", "feita uma"),
                ("feito", "feito_article", "nominal", "feitos uns"),
                ("feito", "feito_article", "nominal", "feitas umas"),
                ("igual", "igual_preposition", "prepositional", "igual a"),
                ("igual", "igual_preposition", "prepositional", "igual ao"),
                ("igual", "igual_preposition", "prepositional", "igual à"),
                ("igual", "igual_preposition", "prepositional", "igual aos"),
                ("igual", "igual_preposition", "prepositional", "igual às"),
                ("igual", "igual_article", "nominal", "igual um"),
                ("igual", "igual_article", "nominal", "igual uma"),
                ("igual", "igual_article", "nominal", "igual uns"),
                ("igual", "igual_article", "nominal", "igual umas"),
                ("igualzinho", "igualzinho_preposition", "prepositional", "igualzinho a"),
                ("igualzinho", "igualzinho_preposition", "prepositional", "igualzinha ao"),
                ("igualzinho", "igualzinho_preposition", "prepositional", "igualzinhos à"),
                ("igualzinho", "igualzinho_preposition", "prepositional", "igualzinhas aos"),
                ("igualzinho", "igualzinho_preposition", "prepositional", "igualzinho às"),
                ("igualzinho", "igualzinho_article", "nominal", "igualzinho um"),
                ("igualzinho", "igualzinho_article", "nominal", "igualzinha uma"),
                ("igualzinho", "igualzinho_article", "nominal", "igualzinhos uns"),
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
        self.assertEqual("tempestade", text[row["char_end"] :].lstrip().split(",")[0])
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

    def test_context_windows_are_capped(self):
        left = "a" * 100
        right = "b" * 130
        rows = extract_candidate_rows("sample.txt", 1, 0, f"{left} como um {right}")

        self.assertEqual("a" * 80, rows[0]["text_before"])
        self.assertEqual("b" * 120, rows[0]["vehicle_raw"])

    def test_candidate_id_is_deterministic_from_provenance_offsets_pattern_and_match(self):
        first = extract_candidate_rows("sample.txt", 1, 0, "Ele corre como um raio")[0]
        second = extract_candidate_rows("sample.txt", 1, 0, "Ele corre como um raio")[0]
        different_offset = extract_candidate_rows("sample.txt", 1, 0, "Agora ele corre como um raio")[0]

        self.assertEqual("6af45e18b1e60a28295a535c952e718ba2ff608f", first["candidate_id"])
        self.assertEqual(first["candidate_id"], second["candidate_id"])
        self.assertNotEqual(first["candidate_id"], different_offset["candidate_id"])


if __name__ == "__main__":
    unittest.main()
