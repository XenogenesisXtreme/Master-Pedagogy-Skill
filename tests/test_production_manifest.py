import json
import tempfile
import unittest
from pathlib import Path

from scripts.production_manifest import make_manifest, select_provider
from scripts.video_explainer import build_storyboard


class ProductionManifestTests(unittest.TestCase):
    def storyboard(self):
        return build_storyboard(
            topic="Rolling Bodies",
            objective="Relate translation and rotation.",
            narration="A body rolls and rotates. Compare its energy terms.",
            mastery_check="Which body reaches the bottom first?",
            duration=15,
            derived=True,
        )

    def test_provider_order_and_selection_are_auditable(self):
        manifest = make_manifest(self.storyboard())
        self.assertEqual(manifest.provider_order, ["local-cinematic", "hosted-provider", "static-svg-fallback"])
        select_provider(manifest, "local-cinematic")
        selected = [item.provider for item in manifest.provider_decisions if item.selected]
        self.assertEqual(selected, ["local-cinematic"])
        self.assertIn("representative-frame-inspection", manifest.quality_gates)

    def test_manifest_round_trips_as_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = make_manifest(self.storyboard()).write(Path(directory) / "production.json")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pipeline"], "master-pedagogy-cinematic-hybrid")
            self.assertEqual(payload["render_runtime"], "python-ffmpeg")
            self.assertEqual(payload["version"], "1.0")


if __name__ == "__main__":
    unittest.main()
