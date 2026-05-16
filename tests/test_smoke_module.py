from pathlib import Path
import unittest

from tal_qual import SAMPLE_TEXT_PATH


class SmokeModuleTest(unittest.TestCase):
    def test_sample_text_path_points_to_tracked_sample(self):
        sample_path = Path(__file__).resolve().parents[1] / SAMPLE_TEXT_PATH

        self.assertTrue(sample_path.exists())
        self.assertIn("como um", sample_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
