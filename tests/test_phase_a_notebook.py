import json
import unittest
from pathlib import Path


class PhaseAValidationNotebookTest(unittest.TestCase):
    def setUp(self):
        self.notebook_path = Path("notebooks/04_phase_a_validation.ipynb")
        self.notebook = json.loads(self.notebook_path.read_text())
        self.source = "\n".join(
            "".join(cell.get("source", [])) for cell in self.notebook["cells"]
        )

    def test_phase_a_validation_notebook_exists_and_is_valid_json(self):
        self.assertEqual(4, self.notebook["nbformat"])
        self.assertGreaterEqual(len(self.notebook["cells"]), 10)

    def test_notebook_loads_or_runs_phase_a_refined_outputs(self):
        self.assertIn("prepare_refined_dataframe_for_tier", self.source)
        self.assertIn("write_refined_parquet", self.source)
        self.assertIn("write_phase_a_csv_outputs", self.source)
        self.assertIn("REFINED_CANDIDATES_NLP_OUTPUT_PATH", self.source)
        self.assertIn("SILVER_OUTPUT_PATH", self.source)

    def test_notebook_covers_required_validation_views(self):
        required_terms = [
            "vehicle_normalized",
            "vehicle_head_lemma",
            "nlp_refinement_scope",
            "Structural Quality Bucket",
            "top_clean_common_noun_vehicle_heads_dataframe",
            "top_chartable_vehicle_heads_dataframe",
            "candidate_full_text",
            "vehicle_raw",
            "vehicle_phrase_nlp",
            "vehicle_head_pos",
            "vehicle_reject_reason",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.source)

    def test_notebook_states_phase_a_is_not_figurative_literal_classification(self):
        self.assertIn("Phase A is structural vehicle refinement", self.source)
        self.assertIn("does not classify candidates as figurative or literal", self.source)

    def test_before_after_chart_handles_empty_refined_rankings(self):
        self.assertIn("plot_ranking_or_empty", self.source)
        self.assertIn("dataframe.empty", self.source)
        self.assertIn("No rows available for this ranking", self.source)

    def test_notebook_preflights_phase_a_parser_availability(self):
        self.assertIn("load_portuguese_parser", self.source)
        self.assertIn("parser_unavailable", self.source)
        self.assertIn("Missing Phase A spaCy parser", self.source)


if __name__ == "__main__":
    unittest.main()
