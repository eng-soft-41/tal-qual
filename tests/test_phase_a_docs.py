import unittest
from pathlib import Path


class PhaseADocumentationTest(unittest.TestCase):
    def setUp(self):
        self.readme = Path("README.md").read_text()
        self.phase_a_spec = Path("docs/specs/0002-mvp-phase-A-nlp-filter.md").read_text()

    def test_readme_documents_phase_a_runtime_outputs_and_validation_results(self):
        required_terms = [
            "Phase A NLP Refinement Layer",
            "TAL_QUAL_PHASE_A_TIER=sample_debug",
            "TAL_QUAL_PHASE_A_TIER=one_shard_refined",
            "data/gold/refined_candidates_nlp",
            "outputs/phase_a_top_clean_common_noun_heads.csv",
            "notebooks/04_phase_a_validation.ipynb",
            "58,797",
            "does not classify candidates as figurative or literal",
            "Ground adjective extraction and LLM classification remain downstream",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assert_contains_phrase(self.readme, term)

    def test_phase_a_spec_matches_implemented_output_contract(self):
        required_terms = [
            "notebooks/04_phase_a_validation.ipynb",
            "outputs/phase_a_top_clean_common_noun_heads.csv",
            "vehicle_phrase_nlp",
            "vehicle_head",
            "structural_quality_bucket",
            "vehicle_is_clean_common_noun",
            "vehicle_is_chartable_vehicle",
            "58,797",
            "27,926",
            "Ground adjective extraction and LLM classification remain downstream",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assert_contains_phrase(self.phase_a_spec, term)

    def assert_contains_phrase(self, content, phrase):
        normalized_content = " ".join(content.split())
        normalized_phrase = " ".join(phrase.split())
        self.assertIn(normalized_phrase, normalized_content)


if __name__ == "__main__":
    unittest.main()
