import json
import tempfile
import unittest
from pathlib import Path

from scripts.video_explainer import (
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    build_storyboard,
    infer_exam_profile,
    render_static_fallback,
    validate_storyboard,
)


class VideoExplainerTests(unittest.TestCase):
    def make_storyboard(self, **overrides):
        values = {
            "topic": "Newton's second law",
            "objective": "Relate force, mass, and acceleration.",
            "narration": "Observe the motion. Define the variables. Derive the relationship. Check the units. Apply the result.",
            "mastery_check": "Predict the acceleration when force doubles.",
            "equations": ["F = ma"],
            "derived": True,
        }
        values.update(overrides)
        return build_storyboard(**values)

    def test_cinematic_is_the_default_and_16_9_is_enforced(self):
        storyboard = self.make_storyboard()
        self.assertEqual(storyboard.style, "cinematic")
        self.assertEqual(storyboard.aspect_ratio, "16:9")
        self.assertEqual(sum(scene.duration for scene in storyboard.scenes), 15)
        self.assertEqual(validate_storyboard(storyboard), [])

    def test_profile_is_inferred_from_topic(self):
        self.assertEqual(infer_exam_profile("Rolling bodies"), "JEE")
        self.assertEqual(infer_exam_profile("Cell biology"), "NEET")
        self.assertEqual(infer_exam_profile("A general concept"), "General / Conceptual Learning")

    def test_learner_analogy_requires_consent_and_uses_interest_seed(self):
        with self.assertRaises(ValueError):
            self.make_storyboard(learner_interest="coding", analogy_consent=True, duration=0)
        storyboard = self.make_storyboard(learner_interest="coding and game development", analogy_consent=True, duration=30)
        self.assertEqual(storyboard.learner_interest, "coding and game development")
        self.assertIsNotNone(storyboard.analogy_seed)
        self.assertTrue(any("learner-provided interest" in check for check in storyboard.scenes[1].validation_checks))
        self.assertIn("Learner-approved analogy seed", storyboard.scenes[1].narration)
        self.assertEqual(sum(scene.duration for scene in storyboard.scenes), 30)

    def test_duration_accepts_arbitrary_positive_values_with_configurable_ceiling(self):
        self.assertEqual(sum(scene.duration for scene in self.make_storyboard(duration=1).scenes), 1)
        self.assertEqual(sum(scene.duration for scene in self.make_storyboard(duration=60).scenes), 60)
        self.assertEqual(sum(scene.duration for scene in self.make_storyboard(duration=120).scenes), 120)
        self.assertEqual(sum(scene.duration for scene in self.make_storyboard(duration=MAX_DURATION_SECONDS).scenes), MAX_DURATION_SECONDS)
        with self.assertRaises(ValueError):
            self.make_storyboard(duration=MIN_DURATION_SECONDS - 1)
        with self.assertRaises(ValueError):
            self.make_storyboard(duration=MAX_DURATION_SECONDS + 1)

    def test_fhp_requires_completed_derivation(self):
        with self.assertRaises(ValueError):
            self.make_storyboard(mode="fhp", style="fhp", derived=False)
        storyboard = self.make_storyboard(mode="fhp", style="fhp", derived=True)
        self.assertEqual(storyboard.mode, "fhp")
        self.assertTrue(all("FHP derivation already completed" in scene.validation_checks for scene in storyboard.scenes))

    def test_static_fallback_writes_scene_assets_and_manifest(self):
        storyboard = self.make_storyboard(style="short")
        with tempfile.TemporaryDirectory() as directory:
            paths = render_static_fallback(storyboard, directory)
            self.assertTrue(any(path.name == "manifest.json" for path in paths))
            scene_paths = [path for path in paths if path.suffix == ".svg"]
            self.assertEqual(len(scene_paths), 3)
            manifest = json.loads(Path(directory, "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["files"]), 3)
            scene_text = Path(scene_paths[0]).read_text(encoding="utf-8")
            self.assertIn("Newton", scene_text)
            self.assertNotIn("M80 760", scene_text)

    def test_hydrostatic_pressure_gets_explanatory_visual_phases(self):
        storyboard = self.make_storyboard(
            topic="Hydrostatic Pressure",
            objective="Derive how pressure changes with depth.",
            narration="Imagine a fluid slab. Compare the forces. Derive delta pressure. Interpret every term. Predict at double depth.",
            equations=["ΔP = F/A", "m = ρAh", "F = mg = ρAhg", "ΔP = ρgh", "P = P₀ + ρgh"],
            duration=30,
            learner_interest="coding and game development",
            analogy_consent=True,
        )
        self.assertTrue(all(scene.visual["kind"] == "hydrostatic" for scene in storyboard.scenes))
        self.assertIn("thin fluid slab", storyboard.scenes[0].visual_goal)
        self.assertIn("P = P₀ + ρgh", storyboard.scenes[2].equations)


if __name__ == "__main__":
    unittest.main()
