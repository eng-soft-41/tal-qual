import unittest

from tal_qual.bare_como_spacy_filter import classify_bare_como_candidate


class BareComoSpacyFilterTest(unittest.TestCase):
    def test_keeps_visual_head_whitelist_without_spacy_doc(self):
        result = classify_bare_como_candidate(
            {
                "vehicle_head_clean": "água",
                "vehicle_text_raw": "água",
                "candidate_full_text": "ficou claro como água",
            }
        )

        self.assertEqual("keep", result["nlp_quality_label"])
        self.assertEqual("visual_head_whitelist", result["nlp_quality_reason"])
        self.assertFalse(result["nlp_needs_review"])

    def test_rejects_role_head_lexicon(self):
        result = classify_bare_como_candidate(
            {
                "vehicle_head_clean": "jogador",
                "vehicle_text_raw": "jogador de futebol",
                "candidate_full_text": "foi brilhante como jogador de futebol",
            }
        )

        self.assertEqual("reject", result["nlp_quality_label"])
        self.assertEqual("role_head_lexicon", result["nlp_quality_reason"])

    def test_reviews_role_context(self):
        result = classify_bare_como_candidate(
            {
                "vehicle_head_clean": "parceiro",
                "vehicle_text_raw": "parceiro estratégico",
                "candidate_full_text": "a empresa trabalha forte como parceiro estratégico",
            }
        )

        self.assertEqual("reject", result["nlp_quality_label"])
        self.assertEqual("role_head_lexicon", result["nlp_quality_reason"])

    def test_rejects_bad_pos_when_doc_is_available(self):
        class Token:
            def __init__(self, text, lemma, pos):
                self.text = text
                self.lemma_ = lemma
                self.pos_ = pos

        result = classify_bare_como_candidate(
            {
                "vehicle_head_clean": "sendo",
                "vehicle_text_raw": "sendo comum",
                "candidate_full_text": "ficou claro como sendo comum",
            },
            doc=[Token("sendo", "ser", "AUX")],
        )

        self.assertEqual("reject", result["nlp_quality_label"])
        self.assertEqual("bad_spacy_pos_aux", result["nlp_quality_reason"])
        self.assertEqual("ser", result["spacy_vehicle_head_lemma"])


if __name__ == "__main__":
    unittest.main()
