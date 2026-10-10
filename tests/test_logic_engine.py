import importlib
import unittest

from scripts.logic_engine import (
    FHP_MODE,
    FHP_PROTOCOL,
    fhp_mode_details,
    generate_mindmap,
    generate_skill_tree,
    resolve_learning_mode,
)


class LogicEngineTests(unittest.TestCase):
    def test_mindmap_is_styled_and_escapes_mermaid_delimiters(self):
        diagram = generate_mindmap(
            'Newton [Dynamics]',
            ['Mass "m"'],
            ['Force {F}', 'Acceleration'],
            ['Acceleration'],
        )
        self.assertIn("flowchart TB", diagram)
        self.assertIn("classDef done", diagram)
        self.assertIn("Newton (Dynamics)", diagram)
        self.assertIn("Force (F)", diagram)
        self.assertNotIn('Force {F}', diagram)
        self.assertIn(":::done", diagram)

    def test_skill_tree_has_stable_statuses(self):
        diagram = generate_skill_tree(
            [{"title": "Foundations", "completed": True}, {"title": "FHP", "completed": False}],
            current_chapter_index=1,
        )
        self.assertIn('C0["✓ Foundations"]:::done', diagram)
        self.assertIn('C1["◆ FHP"]:::current', diagram)
        self.assertIn("C0 --> C1", diagram)

    def test_fhp_is_a_real_mode_contract(self):
        self.assertEqual(resolve_learning_mode("Floathead Physics"), FHP_MODE)
        details = fhp_mode_details()
        self.assertTrue(details["requires_confirmation"])
        self.assertFalse(details["requires_hobby"])
        self.assertEqual(tuple(details["protocol"]), FHP_PROTOCOL)

    def test_legacy_module_uses_canonical_renderer(self):
        legacy = importlib.import_module("script.logic_engine")
        diagram = legacy.generate_mind_map("Topic", {"Prerequisites": ["Basics"], "Core": ["First step"]})
        self.assertIn("classDef root", diagram)
        self.assertIn("First step", diagram)


if __name__ == "__main__":
    unittest.main()
