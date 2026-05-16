import unittest
from unittest.mock import patch

from tal_qual.refinement import (
    ONE_SHARD_REFINED_TIER,
    PHASE_A_QUALITY_BUCKET_COUNTS_OUTPUT_PATH,
    PHASE_A_REFINEMENT_EXAMPLES_OUTPUT_PATH,
    PHASE_A_SCOPE_COUNTS_OUTPUT_PATH,
    PHASE_A_TOP_CHARTABLE_VEHICLE_HEADS_OUTPUT_PATH,
    PHASE_A_TOP_CLEAN_COMMON_NOUN_HEADS_OUTPUT_PATH,
    PHASE_A_TOP_VEHICLE_HEADS_BY_PATTERN_OUTPUT_PATH,
    REFINED_CANDIDATES_NLP_OUTPUT_PATH,
    SAMPLE_DEBUG_TIER,
    build_nlp_parse_text,
    nlp_refinement_scope,
    prepare_refined_dataframe_for_tier,
    refine_candidate_row,
    sample_debug_rows,
    summarize_refined_rows,
    write_phase_a_csv_outputs,
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


def refined_row(
    candidate_id,
    pattern_type="como_article",
    scope="primary_nominal_article",
    bucket="clean_nominal_vehicle",
    head="raio",
    head_lemma="raio",
    head_pos="NOUN",
    clean=True,
    chartable=True,
    phrase="raio forte",
    full_text="Ele corre como um raio forte",
    line=1,
    segment=0,
    char_start=0,
):
    row = silver_row(candidate_id, pattern_type, line=line, segment=segment, char_start=char_start)
    row.update(
        {
            "nlp_refinement_scope": scope,
            "nlp_parse_text": f"{row['matched_text']} {row['vehicle_raw']}",
            "structural_quality_bucket": bucket,
            "vehicle_phrase_nlp": phrase,
            "vehicle_head": head,
            "vehicle_head_lemma": head_lemma,
            "vehicle_head_pos": head_pos,
            "vehicle_phrase_length_tokens": len(phrase.split()),
            "vehicle_extraction_confidence": "noun_chunk",
            "vehicle_is_clean_common_noun": clean,
            "vehicle_is_chartable_vehicle": chartable,
            "vehicle_reject_reason": "" if clean else bucket,
            "candidate_full_text": full_text,
            "vehicle_raw": phrase,
            "vehicle_normalized": phrase.lower(),
        }
    )
    return row


class RefinementTest(unittest.TestCase):
    def test_refined_output_path_matches_phase_a_contract(self):
        self.assertEqual("data/gold/refined_candidates_nlp", str(REFINED_CANDIDATES_NLP_OUTPUT_PATH))
        self.assertEqual("outputs/phase_a_scope_counts.csv", str(PHASE_A_SCOPE_COUNTS_OUTPUT_PATH))
        self.assertEqual(
            "outputs/phase_a_quality_bucket_counts.csv",
            str(PHASE_A_QUALITY_BUCKET_COUNTS_OUTPUT_PATH),
        )
        self.assertEqual(
            "outputs/phase_a_top_clean_common_noun_heads.csv",
            str(PHASE_A_TOP_CLEAN_COMMON_NOUN_HEADS_OUTPUT_PATH),
        )
        self.assertEqual(
            "outputs/phase_a_top_chartable_vehicle_heads.csv",
            str(PHASE_A_TOP_CHARTABLE_VEHICLE_HEADS_OUTPUT_PATH),
        )
        self.assertEqual(
            "outputs/phase_a_top_vehicle_heads_by_pattern.csv",
            str(PHASE_A_TOP_VEHICLE_HEADS_BY_PATTERN_OUTPUT_PATH),
        )
        self.assertEqual("outputs/phase_a_refinement_examples.csv", str(PHASE_A_REFINEMENT_EXAMPLES_OUTPUT_PATH))

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
        self.assertEqual("clean_nominal_vehicle", refined["structural_quality_bucket"])
        self.assertTrue(refined["vehicle_is_clean_common_noun"])
        self.assertTrue(refined["vehicle_is_chartable_vehicle"])
        self.assertEqual("", refined["vehicle_reject_reason"])

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
        self.assertEqual("clean_nominal_vehicle", refined["structural_quality_bucket"])

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
        self.assertEqual("clausal_or_verbal_continuation", refined["structural_quality_bucket"])
        self.assertFalse(refined["vehicle_is_clean_common_noun"])
        self.assertFalse(refined["vehicle_is_chartable_vehicle"])
        self.assertEqual("clausal_or_verbal_continuation", refined["vehicle_reject_reason"])

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
        self.assertEqual("not_in_first_slice_scope", refined["structural_quality_bucket"])
        self.assertFalse(refined["vehicle_is_clean_common_noun"])
        self.assertFalse(refined["vehicle_is_chartable_vehicle"])
        self.assertEqual("not_in_first_slice_scope", refined["vehicle_reject_reason"])

    def test_pronoun_numeric_and_empty_buckets_are_not_chartable(self):
        pronoun = self.refine_with_single_head("candidate-pronoun", "que_nem_bare", "eu", "eu", "PRON")
        numeric = self.refine_with_single_head("candidate-number", "igual_article", "três", "três", "NUM")
        empty = silver_row("candidate-empty", "como_article")
        empty["vehicle_raw"] = ""

        empty_refined = refine_candidate_row(empty, parser=FakeParser(FakeDoc([], [])))

        self.assert_quality(pronoun, "pronoun_vehicle", clean=False, chartable=False)
        self.assertEqual("pronoun_vehicle", pronoun["vehicle_reject_reason"])
        self.assert_quality(numeric, "numeric_vehicle", clean=False, chartable=False)
        self.assertEqual("numeric_vehicle", numeric["vehicle_reject_reason"])
        self.assert_quality(empty_refined, "empty_vehicle", clean=False, chartable=False)
        self.assertEqual("empty_vehicle", empty_refined["vehicle_reject_reason"])

    def test_proper_name_vehicle_is_chartable_but_not_clean_common_noun(self):
        refined = self.refine_with_single_head("candidate-proper", "como_article", "Maria", "Maria", "PROPN")

        self.assert_quality(refined, "proper_name_vehicle", clean=False, chartable=True)
        self.assertEqual("proper_name_vehicle", refined["vehicle_reject_reason"])

    def test_overly_long_and_url_or_symbol_noise_are_excluded(self):
        long_phrase = self.refine_with_phrase(
            "candidate-long",
            "como_article",
            "um caminho cheio de voltas grandes demais agora",
            "caminho",
            "caminho",
            "NOUN",
            7,
        )
        url_noise = self.refine_with_phrase(
            "candidate-url",
            "como_article",
            "http://exemplo.com",
            "http://exemplo.com",
            "http://exemplo.com",
            "NOUN",
            1,
        )

        self.assert_quality(long_phrase, "overly_long_vehicle_phrase", clean=False, chartable=False)
        self.assertEqual("overly_long_vehicle_phrase", long_phrase["vehicle_reject_reason"])
        self.assert_quality(url_noise, "url_or_symbol_noise", clean=False, chartable=False)
        self.assertEqual("url_or_symbol_noise", url_noise["vehicle_reject_reason"])

    def test_quote_and_apostrophe_artifacts_are_excluded_from_vehicle_rankings(self):
        quote_prefixed = self.refine_with_phrase(
            "candidate-quote-prefix",
            "como_article",
            "' espécie",
            "espécie",
            "espécie",
            "NOUN",
            2,
        )
        malformed_apostrophe = self.refine_with_phrase(
            "candidate-malformed-apostrophe",
            "como_article",
            "bunda mole''Ai",
            "mole''Ai",
            "mole''Ai",
            "NOUN",
            2,
        )

        self.assert_quality(quote_prefixed, "url_or_symbol_noise", clean=False, chartable=False)
        self.assertEqual("url_or_symbol_noise", quote_prefixed["vehicle_reject_reason"])
        self.assert_quality(malformed_apostrophe, "url_or_symbol_noise", clean=False, chartable=False)
        self.assertEqual("url_or_symbol_noise", malformed_apostrophe["vehicle_reject_reason"])

    def test_noun_chunk_uses_earlier_noun_when_parser_selects_modifier_like_head(self):
        row = silver_row("candidate-rapper", "como_article")
        row["vehicle_raw"] = "rapper controverso sem medo"
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("como", "como", "SCONJ", 0),
                    FakeToken("um", "um", "DET", 1),
                    FakeToken("rapper", "rapper", "NOUN", 2),
                    FakeToken("controverso", "controverso", "NOUN", 3),
                ],
                [FakeSpan("rapper controverso", 2, 4, FakeToken("controverso", "controverso", "NOUN", 3))],
            )
        )

        refined = refine_candidate_row(row, parser=parser)

        self.assertEqual("rapper controverso", refined["vehicle_phrase_nlp"])
        self.assertEqual("rapper", refined["vehicle_head"])
        self.assertEqual("rapper", refined["vehicle_head_lemma"])
        self.assertEqual("clean_nominal_vehicle", refined["structural_quality_bucket"])

    def test_number_prefixed_noun_phrases_are_not_clean_common_noun_vehicles(self):
        refined = self.refine_with_phrase(
            "candidate-number-prefix",
            "como_article",
            "100 empresas mais confiáveis",
            "empresas",
            "empresa",
            "NOUN",
            4,
        )

        self.assert_quality(refined, "numeric_vehicle", clean=False, chartable=False)
        self.assertEqual("numeric_vehicle", refined["vehicle_reject_reason"])

    def test_uppercase_common_noun_web_noise_is_excluded_but_proper_names_remain_chartable(self):
        uppercase_noise = self.refine_with_single_head(
            "candidate-uppercase-noise",
            "como_article",
            "TOALHAS",
            "toalha",
            "NOUN",
        )
        proper_name = self.refine_with_single_head(
            "candidate-proper-name",
            "como_article",
            "NASA",
            "NASA",
            "PROPN",
        )

        self.assert_quality(uppercase_noise, "url_or_symbol_noise", clean=False, chartable=False)
        self.assertEqual("url_or_symbol_noise", uppercase_noise["vehicle_reject_reason"])
        self.assert_quality(proper_name, "proper_name_vehicle", clean=False, chartable=True)
        self.assertEqual("proper_name_vehicle", proper_name["vehicle_reject_reason"])

    def test_bare_connector_artifact_sequer_is_not_chartable(self):
        refined = self.refine_with_single_head("candidate-sequer", "que_nem_bare", "sequer", "sequer", "NOUN")

        self.assert_quality(refined, "parser_uncertain", clean=False, chartable=False)
        self.assertEqual("parser_uncertain", refined["vehicle_reject_reason"])

    def test_parser_uncertain_bucket_is_used_when_parser_is_unavailable(self):
        row = silver_row("candidate-parser", "como_article")

        with patch("tal_qual.refinement.load_portuguese_parser", return_value=UnavailableFakeParser()):
            refined = refine_candidate_row(row)

        self.assert_quality(refined, "parser_uncertain", clean=False, chartable=False)
        self.assertEqual("parser_uncertain", refined["vehicle_reject_reason"])

    def test_role_or_classification_risk_is_marked_without_deleting_row(self):
        row = silver_row("candidate-role", "como_article")
        row["text_before"] = "Ele trabalha"
        row["vehicle_raw"] = "advogado"
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("como", "como", "SCONJ", 0),
                    FakeToken("um", "um", "DET", 1),
                    FakeToken("advogado", "advogado", "NOUN", 2),
                ],
                [FakeSpan("advogado", 2, 3, FakeToken("advogado", "advogado", "NOUN", 2))],
            )
        )

        refined = refine_candidate_row(row, parser=parser)

        self.assertEqual("candidate-role", refined["candidate_id"])
        self.assert_quality(refined, "role_or_classification_risk", clean=False, chartable=False)
        self.assertEqual("role_or_classification_risk", refined["vehicle_reject_reason"])

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

    def test_phase_a_row_summaries_count_scopes_buckets_and_vehicle_head_lemmas(self):
        rows = [
            refined_row(
                "clean-1",
                pattern_type="como_article",
                scope="primary_nominal_article",
                bucket="clean_nominal_vehicle",
                head_lemma="raio",
                clean=True,
                chartable=True,
                phrase="raio forte",
                full_text="Ele corre como um raio forte",
            ),
            refined_row(
                "clean-2",
                pattern_type="que_nem_bare",
                scope="primary_nominal_bare",
                bucket="clean_nominal_vehicle",
                head_lemma="raio",
                clean=True,
                chartable=True,
                phrase="raio claro",
                full_text="Ela chega que nem raio claro",
            ),
            refined_row(
                "proper-1",
                pattern_type="como_article",
                scope="primary_nominal_article",
                bucket="proper_name_vehicle",
                head="Maria",
                head_lemma="Maria",
                head_pos="PROPN",
                clean=False,
                chartable=True,
                phrase="Maria",
                full_text="Fala como uma Maria",
            ),
            refined_row(
                "pronoun-1",
                pattern_type="que_nem_bare",
                scope="primary_nominal_bare",
                bucket="pronoun_vehicle",
                head="eu",
                head_lemma="eu",
                head_pos="PRON",
                clean=False,
                chartable=False,
                phrase="eu",
                full_text="Canta que nem eu",
            ),
        ]

        summaries = summarize_refined_rows(rows)

        self.assertEqual(
            [
                {"nlp_refinement_scope": "primary_nominal_article", "count": 2},
                {"nlp_refinement_scope": "primary_nominal_bare", "count": 2},
            ],
            summaries["scope_counts"],
        )
        self.assertEqual(
            [
                {"structural_quality_bucket": "clean_nominal_vehicle", "count": 2},
                {"structural_quality_bucket": "pronoun_vehicle", "count": 1},
                {"structural_quality_bucket": "proper_name_vehicle", "count": 1},
            ],
            summaries["quality_bucket_counts"],
        )
        self.assertEqual(
            [
                {
                    "vehicle_head_lemma": "raio",
                    "occurrence_count": 2,
                    "distinct_candidate_text_count": 2,
                    "distinct_refined_phrase_count": 2,
                    "representative_vehicle_head": "raio",
                    "representative_vehicle_phrase": "raio claro",
                }
            ],
            summaries["top_clean_common_noun_heads"],
        )
        self.assertEqual(
            ["raio", "Maria"],
            [row["vehicle_head_lemma"] for row in summaries["top_chartable_vehicle_heads"]],
        )
        self.assertEqual(
            [("como_article", "Maria"), ("como_article", "raio"), ("que_nem_bare", "raio")],
            [(row["pattern_type"], row["vehicle_head_lemma"]) for row in summaries["top_vehicle_heads_by_pattern"]],
        )

    def test_phase_a_refinement_examples_are_side_by_side_deterministic_and_deduplicated(self):
        rows = [
            refined_row("late", line=3, char_start=8, full_text="repete como um raio"),
            refined_row("early", line=1, char_start=2, full_text="repete como um raio"),
            refined_row("kept", line=2, char_start=1, full_text="grita como um trovão", head_lemma="trovão"),
        ]

        examples = summarize_refined_rows(rows, examples_per_pattern_bucket=2)["refinement_examples"]

        self.assertEqual(["early", "kept"], [row["candidate_id"] for row in examples])
        self.assertEqual(
            [
                "vehicle_raw",
                "vehicle_normalized",
                "vehicle_phrase_nlp",
                "vehicle_head",
                "vehicle_head_lemma",
            ],
            [
                column
                for column in examples[0]
                if column
                in {
                    "vehicle_raw",
                    "vehicle_normalized",
                    "vehicle_phrase_nlp",
                    "vehicle_head",
                    "vehicle_head_lemma",
                }
            ],
        )
        self.assertEqual([1, 2], [row["example_rank"] for row in examples])

    def test_phase_a_csv_writer_emits_all_expected_outputs(self):
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
            def __init__(self, name="refined"):
                self.name = name
                self.write = FakeWriter(name)

        with (
            patch("tal_qual.refinement.refinement_scope_counts_dataframe", return_value=FakeDataFrame("scope_counts")),
            patch(
                "tal_qual.refinement.structural_quality_bucket_counts_dataframe",
                return_value=FakeDataFrame("quality_bucket_counts"),
            ),
            patch(
                "tal_qual.refinement.top_clean_common_noun_vehicle_heads_dataframe",
                return_value=FakeDataFrame("top_clean_heads"),
            ),
            patch(
                "tal_qual.refinement.top_chartable_vehicle_heads_dataframe",
                return_value=FakeDataFrame("top_chartable_heads"),
            ),
            patch(
                "tal_qual.refinement.top_vehicle_heads_by_pattern_dataframe",
                return_value=FakeDataFrame("top_heads_by_pattern"),
            ),
            patch("tal_qual.refinement.refinement_examples_dataframe", return_value=FakeDataFrame("examples")),
        ):
            write_phase_a_csv_outputs(FakeDataFrame(), examples_per_pattern_bucket=3)

        self.assertEqual(
            [
                ("scope_counts", "outputs/phase_a_scope_counts.csv", "overwrite", ("header", True)),
                (
                    "quality_bucket_counts",
                    "outputs/phase_a_quality_bucket_counts.csv",
                    "overwrite",
                    ("header", True),
                ),
                (
                    "top_clean_heads",
                    "outputs/phase_a_top_clean_common_noun_heads.csv",
                    "overwrite",
                    ("header", True),
                ),
                (
                    "top_chartable_heads",
                    "outputs/phase_a_top_chartable_vehicle_heads.csv",
                    "overwrite",
                    ("header", True),
                ),
                (
                    "top_heads_by_pattern",
                    "outputs/phase_a_top_vehicle_heads_by_pattern.csv",
                    "overwrite",
                    ("header", True),
                ),
                ("examples", "outputs/phase_a_refinement_examples.csv", "overwrite", ("header", True)),
            ],
            written_paths,
        )

    def refine_with_single_head(self, candidate_id, pattern_type, text, lemma, pos):
        return self.refine_with_phrase(candidate_id, pattern_type, text, text, lemma, pos, 1)

    def refine_with_phrase(self, candidate_id, pattern_type, phrase, head_text, head_lemma, head_pos, length):
        row = silver_row(candidate_id, pattern_type)
        row["vehicle_raw"] = phrase
        parser = FakeParser(
            FakeDoc(
                [
                    FakeToken("como", "como", "SCONJ", 0),
                    FakeToken("um", "um", "DET", 1),
                    *[FakeToken(f"token-{index}", f"token-{index}", "ADJ", index) for index in range(2, 2 + length)],
                ],
                [FakeSpan(phrase, 2, 2 + length, FakeToken(head_text, head_lemma, head_pos, 2))],
            )
        )
        return refine_candidate_row(row, parser=parser)

    def assert_quality(self, refined, bucket, clean, chartable):
        self.assertEqual(bucket, refined["structural_quality_bucket"])
        self.assertEqual(clean, refined["vehicle_is_clean_common_noun"])
        self.assertEqual(chartable, refined["vehicle_is_chartable_vehicle"])


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


class UnavailableFakeParser:
    model_name = "pt_core_news_sm"
    model_version = ""
    parser_unavailable = True


if __name__ == "__main__":
    unittest.main()
