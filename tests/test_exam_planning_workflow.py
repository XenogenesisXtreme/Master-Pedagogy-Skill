import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / "references" / "exam_planning_workflow.md").read_text(encoding="utf-8")


class ExamPlanningWorkflowTests(unittest.TestCase):
    def test_skill_loads_workflow_when_exam_syllabus_and_date_are_given(self):
        self.assertIn("references/exam_planning_workflow.md", SKILL)
        self.assertIn("exam syllabus and date", SKILL)
        self.assertIn("begin the first scheduled diagnostic or lesson", SKILL)

    def test_workflow_uses_all_three_scope_labels_and_separate_readiness(self):
        for label in ("Core Preparation", "Useful Extension", "Beyond Target Level"):
            self.assertIn(label, WORKFLOW)
        self.assertIn("Exam relevance", WORKFLOW)
        self.assertIn("Learner readiness", WORKFLOW)
        self.assertIn("scope_class", WORKFLOW)
        self.assertIn("readiness_status", WORKFLOW)

    def test_workflow_checks_official_sources_and_ends_before_exam_day(self):
        self.assertIn("current official exam authority", WORKFLOW)
        self.assertIn("through the day before the exam", WORKFLOW)
        self.assertIn("Do not put new learning on the exam day by default", WORKFLOW)

    def test_workflow_collects_every_chapter_status_in_a_manageable_batch(self):
        self.assertIn("for **each** chapter", WORKFLOW)
        self.assertIn("single grouped reply", WORKFLOW)
        self.assertIn("batch by subject", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
