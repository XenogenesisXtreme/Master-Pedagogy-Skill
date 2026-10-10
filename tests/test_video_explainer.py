import json
import tempfile
import unittest
from pathlib import Path

from scripts.video_explainer import (
    build_storyboard,
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

    def test_whiteboard_storyboard_is_16_9_and_long_enough(self):
        storyboard = self.make_storyboard()
        self.assertEqual(storyboard.aspect_ratio, "16:9")
        self.assertEqual(storyboard.style, "whiteboard")
        self.assertGreaterEqual(sum(scene.duration for scene in storyboard.scenes), 10)
        self.assertEqual(validate_storyboard(storyboard), [])

    def test_fhp_requires_completed_derivation(self):
        with self.assertRaises(ValueError):
            self.make_storyboard(mode="fhp", derived=False)
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
            self.assertIn("Newton", Path(scene_paths[0]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
