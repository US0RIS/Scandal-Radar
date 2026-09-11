import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "rank_candidates.py"
spec = importlib.util.spec_from_file_location("rank_candidates", SCRIPT)
rank_candidates = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(rank_candidates)


class ScoringTests(unittest.TestCase):
    def test_weights_sum_to_100(self):
        self.assertEqual(sum(rank_candidates.WEIGHTS.values()), 100)

    def test_registry_is_valid(self):
        rows = rank_candidates.load_candidates(ROOT / "data" / "candidates.csv")
        self.assertEqual(rank_candidates.validate_scores(rows), [])
        self.assertGreaterEqual(len(rows), 20)

    def test_merlin_seed_score(self):
        rows = rank_candidates.load_candidates(ROOT / "data" / "candidates.csv")
        merlin = next(row for row in rows if row["name"] == "Merlin AI")
        self.assertEqual(float(merlin["computed_score"]), 90.4)

    def test_score_bounds(self):
        rows = rank_candidates.load_candidates(ROOT / "data" / "candidates.csv")
        for row in rows:
            score = float(row["computed_score"])
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)


if __name__ == "__main__":
    unittest.main()
