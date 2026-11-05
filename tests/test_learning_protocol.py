import unittest

from scripts.learning_protocol import (
    DIFFICULTY_LEVELS,
    ERROR_CATEGORIES,
    PROBLEM_SOLVING_STEPS,
    TEACHING_SEQUENCE,
    build_micro_lesson_plan,
    classify_error,
    next_difficulty_level,
    remediation_plan,
)


class LearningProtocolTests(unittest.TestCase):
    def test_default_sequence_is_intuition_to_mastery(self):
        self.assertEqual(TEACHING_SEQUENCE, (
            "intuition", "physical_understanding", "concept", "equation", "application", "mastery"
        ))

    def test_numerical_plan_includes_eight_problem_solving_steps(self):
        plan = build_micro_lesson_plan("rolling motion", level=3, numerical=True)
        self.assertEqual(plan["difficulty_name"], "application")
        self.assertEqual(plan["problem_solving_steps"], list(PROBLEM_SOLVING_STEPS))
        self.assertEqual(plan["steps"], list(TEACHING_SEQUENCE))

    def test_difficulty_advances_only_on_evidence(self):
        self.assertEqual(next_difficulty_level(2, demonstrated_mastery=False), 2)
        self.assertEqual(next_difficulty_level(2, demonstrated_mastery=True), 3)
        self.assertEqual(next_difficulty_level(3, demonstrated_mastery=False, consecutive_misses=2), 2)
        self.assertEqual(next_difficulty_level(5, demonstrated_mastery=True), 5)

    def test_error_taxonomy_and_remediation_are_stable(self):
        self.assertEqual(classify_error("I converted cm to m incorrectly"), "unit_conversion")
        self.assertEqual(classify_error("I chose the wrong formula"), "equation_selection")
        self.assertEqual(classify_error("I do not understand why this happens"), "conceptual_misunderstanding")
        for category in ERROR_CATEGORIES:
            self.assertTrue(remediation_plan(category))

    def test_invalid_levels_are_rejected(self):
        self.assertEqual(set(DIFFICULTY_LEVELS), {1, 2, 3, 4, 5})
        with self.assertRaises(ValueError):
            build_micro_lesson_plan("concept", level=6)
        with self.assertRaises(ValueError):
            next_difficulty_level(0, demonstrated_mastery=True)


if __name__ == "__main__":
    unittest.main()
