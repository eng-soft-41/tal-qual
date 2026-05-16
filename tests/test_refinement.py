import unittest
from unittest.mock import patch

from tal_qual.refinement import (
    ONE_SHARD_REFINED_TIER,
    REFINED_CANDIDATES_NLP_OUTPUT_PATH,
    SAMPLE_DEBUG_TIER,
    build_nlp_parse_text,
    nlp_refinement_scope,
    prepare_refined_dataframe_for_tier,
    refine_candidate_row,
    sample_debug_rows,
    write_refined_parquet,
)


def silver_row(candidate_id, pattern_type, source_file="sample.txt", line=1, segment=0, char_start=0):
    return {
        "source_file": source_file,
        "original_line_id": line,
        "segment_id": segment,
        "candidate_id": candidate_id,
        "connector_family": pattern_type.split("_")[0],
        "pattern_type": pattern_type,
        "comparison_form": "nominal",
        "matched_text": "como um",
        "text_before": "Ele corre",
        "vehicle_raw": "  raio forte  ",
        "vehicle_normalized": "raio forte",
        "candidate_full_text": "Ele corre como um raio forte",
        "char_start": char_start,
        "char_end": char_start + 7,
    }


class RefinementTest(unittest.TestCase):
    def test_refined_output_path_matches_phase_a_contract(self):
        self.assertEqual("data/gold/refined_candidates_nlp", str(REFINED_CANDIDATES_NLP_OUTPUT_PATH))

    def test_scope_mapping_covers_first_phase_pattern_families(self):
        self.assertEqual("primary_nominal_article", nlp_refinement_scope("como_article"))
        self.assertEqual("primary_nominal_article", nlp_refinement_scope("feito_article"))
        self.assertEqual("primary_nominal_article", nlp_refinement_scope("parecer_article"))
        self.assertEqual("primary_nominal_article", nlp_refinement_scope("igual_article"))
        self.assertEqual("primary_nominal_article", nlp_refinement_scope("igualzinho_article"))
        self.assertEqual("primary_nominal_bare", nlp_refinement_scope("que_nem_bare"))
        self.assertEqual("primary_nominal_bare", nlp_refinement_scope("tal_qual_bare"))
        self.assertEqual("clausal", nlp_refinement_scope("como_se"))
        self.assertEqual("prepositional", nlp_refinement_scope("igual_preposition"))
        self.assertEqual("prepositional", nlp_refinement_scope("igualzinho_preposition"))

    def test_unknown_patterns_are_carried_as_out_of_scope(self):
        self.assertEqual("not_in_first_slice_scope", nlp_refinement_scope("future_pattern"))

    def test_parse_text_is_connector_plus_raw_vehicle_with_compacted_whitespace(self):
        self.assertEqual("como um raio forte", build_nlp_parse_text(" como   um ", "  raio   forte "))
        self.assertEqual("como se", build_nlp_parse_text("como se", "   "))

    def test_refined_row_preserves_silver_identity_and_traceability_fields(self):
        row = silver_row("candidate-1", "como_article", char_start=12)

        refined = refine_candidate_row(row)

        self.assertEqual(row["candidate_id"], refined["candidate_id"])
        self.assertEqual(row["source_file"], refined["source_file"])
        self.assertEqual(row["original_line_id"], refined["original_line_id"])
        self.assertEqual(row["segment_id"], refined["segment_id"])
        self.assertEqual(row["char_start"], refined["char_start"])
        self.assertEqual(row["char_end"], refined["char_end"])
        self.assertEqual(row["vehicle_raw"], refined["vehicle_raw"])
        self.assertEqual("primary_nominal_article", refined["nlp_refinement_scope"])
        self.assertEqual("como um raio forte", refined["nlp_parse_text"])

    def test_sample_debug_rows_are_deterministic_and_pattern_stratified(self):
        rows = [
            silver_row("bare-2", "que_nem_bare", line=3, char_start=9),
            silver_row("article-2", "como_article", line=2, char_start=4),
            silver_row("prep-1", "igual_preposition", line=1, char_start=6),
            silver_row("article-1", "como_article", line=1, char_start=8),
            silver_row("bare-1", "que_nem_bare", line=1, char_start=2),
            silver_row("article-3", "como_article", line=3, char_start=1),
        ]

        first = sample_debug_rows(rows, rows_per_pattern=2)
        second = sample_debug_rows(reversed(rows), rows_per_pattern=2)

        self.assertEqual([row["candidate_id"] for row in first], [row["candidate_id"] for row in second])
        self.assertEqual(
            ["article-1", "article-2", "prep-1", "bare-1", "bare-2"],
            [row["candidate_id"] for row in first],
        )

    def test_run_tier_dispatch_supports_sample_debug_and_one_shard_refined(self):
        silver_df = object()
        sample_result = object()
        full_result = object()

        with (
            patch("tal_qual.refinement.prepare_sample_debug_dataframe", return_value=sample_result) as sample,
            patch("tal_qual.refinement.prepare_refined_dataframe", return_value=full_result) as full,
        ):
            self.assertIs(sample_result, prepare_refined_dataframe_for_tier(silver_df, SAMPLE_DEBUG_TIER, 3))
            self.assertIs(full_result, prepare_refined_dataframe_for_tier(silver_df, ONE_SHARD_REFINED_TIER))

        sample.assert_called_once_with(silver_df, 3)
        full.assert_called_once_with(silver_df)

    def test_refined_writer_emits_parquet(self):
        writes = []

        class FakeWriter:
            def mode(self, mode):
                self.mode_value = mode
                return self

            def parquet(self, path):
                writes.append((path, self.mode_value))

        class FakeDataFrame:
            write = FakeWriter()

        write_refined_parquet(FakeDataFrame(), "target/path", mode="append")

        self.assertEqual([("target/path", "append")], writes)


if __name__ == "__main__":
    unittest.main()
