import unittest

from scripts.quiz_module import ComboState


class ComboStateTests(unittest.TestCase):
    def test_four_quick_clears_reach_two_x_after_one_point_five_x_expires(self):
        combo = ComboState()

        statuses = [combo.record_clear(45, correct=True) for _ in range(4)]

        self.assertEqual(
            statuses,
            ["building", "activate_1.5x", "expired", "upgrade_to_2x"],
        )
        self.assertEqual(combo.get_multiplier(), 2.0)
        self.assertEqual(combo.remaining_boosted_uses, 3)
        self.assertEqual(combo.consecutive_quick_clears, 4)

        self.assertEqual(combo.record_clear(45, correct=True), "x2.0")
        self.assertEqual(combo.record_clear(45, correct=True), "x2.0")
        self.assertEqual(combo.record_clear(45, correct=True), "expired")
        self.assertEqual(combo.get_multiplier(), 1.0)
        self.assertEqual(combo.consecutive_quick_clears, 0)


if __name__ == "__main__":
    unittest.main()
