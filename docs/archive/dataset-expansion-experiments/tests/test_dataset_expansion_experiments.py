import unittest
from types import ModuleType
from unittest.mock import patch

from tal_qual.dataset_expansion_experiments import (
    EXPERIMENT_SLUGS,
    accepted_candidates_dataframe,
    accepted_review_sample_dataframe,
    experiment_dataset_path,
    experiment_output_path,
    extract_dataset_expansion_rows,
    prefilter_dataset_expansion_bronze_dataframe,
)


class DatasetExpansionExperimentsTest(unittest.TestCase):
    def test_output_paths_are_grouped_by_experiment_slug(self):
        self.assertEqual(
            "data/gold/experiments/bare_como_curated_ground/candidates",
            str(experiment_dataset_path("bare_como_curated_ground")),
        )
        self.assertEqual(
            "outputs/experiments/bare_como_curated_ground",
            str(experiment_output_path("bare_como_curated_ground")),
        )

    def test_bare_como_excludes_article_connectors_and_keeps_raw_cleanup_fields(self):
        rows = extract_dataset_expansion_rows(
            "sample.txt",
            1,
            0,
            "O quarto estava frio como gelo, mas era limpo.",
            "o quarto estava frio como gelo, mas era limpo.",
            "bare_como_curated_ground",
        )
        article_rows = extract_dataset_expansion_rows(
            "sample.txt",
            1,
            0,
            "Sentia-se forte como um touro.",
            "sentia-se forte como um touro.",
            "bare_como_curated_ground",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual([], article_rows)
        row = rows[0]
        self.assertEqual("bare_como_curated_ground", row["pattern_type"])
        self.assertEqual("como", row["connector_text"])
        self.assertEqual("frio", row["ground_lemma"])
        self.assertEqual("gelo", row["vehicle_text_raw"])
        self.assertEqual("gelo", row["vehicle_text_clean"])
        self.assertEqual("gelo", row["vehicle_head_clean"])
        self.assertEqual("keep", row["quality_label"])
        self.assertEqual("short_vehicle", row["quality_reason"])
        self.assertFalse(row["needs_review"])

    def test_bare_como_v2_strips_definite_article_vehicle_head(self):
        rows = extract_dataset_expansion_rows(
            "sample.txt",
            1,
            0,
            "O menino ficou forte como o pai.",
            "o menino ficou forte como o pai.",
            "bare_como_curated_ground_v2",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("o pai", rows[0]["vehicle_text_raw"])
        self.assertEqual("pai", rows[0]["vehicle_text_clean"])
        self.assertEqual("pai", rows[0]["vehicle_head_clean"])
        self.assertEqual("keep", rows[0]["quality_label"])
        self.assertEqual("stripped_definite_article", rows[0]["quality_reason"])

    def test_bare_como_v2_rejects_clause_like_starts(self):
        rows = extract_dataset_expansion_rows(
            "sample.txt",
            1,
            0,
            "Ficou claro como se nada tivesse acontecido.",
            "ficou claro como se nada tivesse acontecido.",
            "bare_como_curated_ground_v2",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("reject", rows[0]["quality_label"])
        self.assertEqual("bad_vehicle_start", rows[0]["quality_reason"])

    def test_bare_como_v2_rejects_possessive_and_adverb_heads(self):
        for text, head in [
            ("Ficou doce como seu gesto.", "seu"),
            ("Está forte como agora parecia.", "agora"),
            ("Era grande como quando saiu.", "quando"),
            ("Ficou leve como mais ninguém.", "mais"),
        ]:
            with self.subTest(head=head):
                rows = extract_dataset_expansion_rows(
                    "sample.txt",
                    1,
                    0,
                    text,
                    text.lower(),
                    "bare_como_curated_ground_v2",
                )

                self.assertEqual(1, len(rows))
                self.assertEqual(head, rows[0]["vehicle_head_clean"])
                self.assertEqual("reject", rows[0]["quality_label"])
                self.assertEqual("bad_vehicle_start", rows[0]["quality_reason"])

    def test_colloquial_connectors_trim_clause_like_tails(self):
        rows = extract_dataset_expansion_rows(
            "sample.txt",
            1,
            0,
            "Ele corre feito louco quando chove.",
            "ele corre feito louco quando chove.",
            "colloquial_que_nem_feito",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("feito", rows[0]["connector_text"])
        self.assertEqual("louco", rows[0]["vehicle_text_clean"])
        self.assertEqual("louco quando chove", rows[0]["vehicle_text_raw"])
        self.assertEqual("trimmed", rows[0]["quality_label"])
        self.assertEqual("trimmed_clause_like_tail", rows[0]["quality_reason"])

    def test_broader_ground_window_uses_curated_ground_not_intensifier(self):
        rows = extract_dataset_expansion_rows(
            "sample.txt",
            1,
            0,
            "O tecido parecia tão leve como uma pluma.",
            "o tecido parecia tão leve como uma pluma.",
            "broader_ground_window_como_article",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("leve", rows[0]["ground_text"])
        self.assertEqual("leve", rows[0]["ground_lemma"])
        self.assertEqual("como uma", rows[0]["connector_text"])
        self.assertEqual("pluma", rows[0]["vehicle_head_clean"])

    def test_prefilter_uses_native_match_text_rlike_for_each_experiment(self):
        class FakeColumn:
            def __init__(self):
                self.pattern = None

            def rlike(self, pattern):
                self.pattern = pattern
                return ("rlike", "match_text", pattern)

        class FakeDataFrame:
            def __init__(self):
                self.condition = None

            def where(self, condition):
                self.condition = condition
                return self

        fake_column = FakeColumn()
        pyspark_module = ModuleType("pyspark")
        sql_module = ModuleType("pyspark.sql")
        functions_module = ModuleType("pyspark.sql.functions")
        functions_module.col = lambda name: fake_column

        with patch.dict(
            "sys.modules",
            {
                "pyspark": pyspark_module,
                "pyspark.sql": sql_module,
                "pyspark.sql.functions": functions_module,
            },
        ):
            for slug in EXPERIMENT_SLUGS:
                fake_df = FakeDataFrame()
                self.assertIs(fake_df, prefilter_dataset_expansion_bronze_dataframe(fake_df, slug))
                self.assertEqual(("rlike", "match_text", fake_column.pattern), fake_df.condition)
                self.assertIn("forte", fake_column.pattern)

    def test_accepted_candidates_filter_keeps_only_keep_and_trimmed(self):
        class FakeColumn:
            def __init__(self, name):
                self.name = name

            def isin(self, *values):
                return ("isin", self.name, values)

        class FakeDataFrame:
            def __init__(self):
                self.condition = None

            def where(self, condition):
                self.condition = condition
                return self

        fake_df = FakeDataFrame()
        pyspark_module = ModuleType("pyspark")
        sql_module = ModuleType("pyspark.sql")
        functions_module = ModuleType("pyspark.sql.functions")
        functions_module.col = lambda name: FakeColumn(name)

        with patch.dict(
            "sys.modules",
            {
                "pyspark": pyspark_module,
                "pyspark.sql": sql_module,
                "pyspark.sql.functions": functions_module,
            },
        ):
            self.assertIs(fake_df, accepted_candidates_dataframe(fake_df))

        self.assertEqual(("isin", "quality_label", ("keep", "trimmed")), fake_df.condition)

    def test_accepted_review_sample_uses_accepted_filter(self):
        calls = []

        class FakeColumn:
            def __init__(self, name):
                self.name = name

            def desc(self):
                return ("desc", self.name)

            def isin(self, *values):
                return ("isin", self.name, values)

        class FakeExpression:
            def __init__(self, value):
                self.value = value

            def desc(self):
                return ("desc", self.value)

        class FakeDataFrame:
            def where(self, condition):
                calls.append(("where", condition))
                return self

            def select(self, *columns):
                calls.append(("select", columns))
                return self

            def orderBy(self, *columns):
                calls.append(("orderBy", columns))
                return self

            def limit(self, limit):
                calls.append(("limit", limit))
                return self

        pyspark_module = ModuleType("pyspark")
        sql_module = ModuleType("pyspark.sql")
        functions_module = ModuleType("pyspark.sql.functions")
        functions_module.col = lambda name: FakeColumn(name)
        functions_module.length = lambda column: FakeExpression(("length", column.name))

        fake_df = FakeDataFrame()
        with patch.dict(
            "sys.modules",
            {
                "pyspark": pyspark_module,
                "pyspark.sql": sql_module,
                "pyspark.sql.functions": functions_module,
            },
        ):
            self.assertIs(fake_df, accepted_review_sample_dataframe(fake_df, limit=25))

        self.assertIn(("where", ("isin", "quality_label", ("keep", "trimmed"))), calls)
        self.assertIn(("limit", 25), calls)


if __name__ == "__main__":
    unittest.main()
