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

    def test_article_candidate_prefers_noun_chunk_vehicle_extraction(self):
        row = silver_row("candidate-1", "como_article")
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("como", "como", "SCONJ", 0),
                    FakeToken("um", "um", "DET", 1),
                    FakeToken("raio", "raio", "NOUN", 2),
                    FakeToken("forte", "forte", "ADJ", 3),
                ],
                [FakeSpan("raio forte", 2, 4, FakeToken("raio", "raio", "NOUN", 2))],
            )
        )

        refined = refine_candidate_row(row, parser=parser)

        self.assertEqual("raio forte", refined["vehicle_phrase_nlp"])
        self.assertEqual("raio", refined["vehicle_head"])
        self.assertEqual("raio", refined["vehicle_head_lemma"])
        self.assertEqual("NOUN", refined["vehicle_head_pos"])
        self.assertEqual(2, refined["vehicle_phrase_length_tokens"])
        self.assertEqual("noun_chunk", refined["vehicle_extraction_confidence"])
        self.assertEqual("fake_pt", refined["nlp_model_name"])
        self.assertEqual("0.1", refined["nlp_model_version"])

    def test_bare_candidate_uses_pos_fallback_and_keeps_bare_scope(self):
        row = silver_row("candidate-2", "que_nem_bare")
        row["matched_text"] = "que nem"
        row["vehicle_raw"] = "gente grande"
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("que", "que", "SCONJ", 0),
                    FakeToken("nem", "nem", "ADV", 1),
                    FakeToken("gente", "gente", "NOUN", 2),
                    FakeToken("grande", "grande", "ADJ", 3),
                ],
                [],
            )
        )

        refined = refine_candidate_row(row, parser=parser)

        self.assertEqual("primary_nominal_bare", refined["nlp_refinement_scope"])
        self.assertEqual("gente grande", refined["vehicle_phrase_nlp"])
        self.assertEqual("gente", refined["vehicle_head"])
        self.assertEqual("gente", refined["vehicle_head_lemma"])
        self.assertEqual("NOUN", refined["vehicle_head_pos"])
        self.assertEqual(2, refined["vehicle_phrase_length_tokens"])
        self.assertEqual("pos_fallback", refined["vehicle_extraction_confidence"])

    def test_target_scope_without_noun_like_vehicle_keeps_empty_structure_fields(self):
        row = silver_row("candidate-3", "como_article")
        row["vehicle_raw"] = "correndo muito"
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("como", "como", "SCONJ", 0),
                    FakeToken("um", "um", "DET", 1),
                    FakeToken("correndo", "correr", "VERB", 2),
                    FakeToken("muito", "muito", "ADV", 3),
                ],
                [],
            )
        )

        refined = refine_candidate_row(row, parser=parser)

        self.assertEqual("", refined["vehicle_phrase_nlp"])
        self.assertEqual("", refined["vehicle_head"])
        self.assertEqual("", refined["vehicle_head_lemma"])
        self.assertEqual("", refined["vehicle_head_pos"])
        self.assertEqual(0, refined["vehicle_phrase_length_tokens"])
        self.assertEqual("no_noun_like_vehicle", refined["vehicle_extraction_confidence"])

    def test_non_target_scope_is_carried_without_default_vehicle_extraction(self):
        row = silver_row("candidate-4", "como_se")
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("como", "como", "SCONJ", 0),
                    FakeToken("se", "se", "SCONJ", 1),
                    FakeToken("fosse", "ser", "VERB", 2),
                    FakeToken("rei", "rei", "NOUN", 3),
                ],
                [FakeSpan("rei", 3, 4, FakeToken("rei", "rei", "NOUN", 3))],
            )
        )

        refined = refine_candidate_row(row, parser=parser)

        self.assertEqual("clausal", refined["nlp_refinement_scope"])
        self.assertEqual("", refined["vehicle_phrase_nlp"])
        self.assertEqual("", refined["vehicle_head"])
        self.assertEqual("", refined["vehicle_head_lemma"])
        self.assertEqual("", refined["vehicle_head_pos"])
        self.assertEqual(0, refined["vehicle_phrase_length_tokens"])
        self.assertEqual("not_in_first_slice_scope", refined["vehicle_extraction_confidence"])
        self.assertEqual("fake_pt", refined["nlp_model_name"])
        self.assertEqual("0.1", refined["nlp_model_version"])

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


class FakeToken:
    def __init__(self, text, lemma, pos, index):
        self.text = text
        self.lemma_ = lemma
        self.pos_ = pos
        self.i = index


class FakeSpan:
    def __init__(self, text, start, end, root):
        self.text = text
        self.start = start
        self.end = end
        self.root = root

    def __len__(self):
        return self.end - self.start


class FakeDoc:
    def __init__(self, tokens, noun_chunks):
        self._tokens = tokens
        self.noun_chunks = noun_chunks

    def __iter__(self):
        return iter(self._tokens)

    def __getitem__(self, index):
        return self._tokens[index]

    def __len__(self):
        return len(self._tokens)


class FakeParser:
    model_name = "fake_pt"
    model_version = "0.1"

    def __init__(self, doc):
        self.doc = doc

    def __call__(self, text):
        self.text = text
        return self.doc


if __name__ == "__main__":
    unittest.main()
