import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.hybrid_video import render_hybrid, render_local_cinematic, render_result_manifest
from scripts.video_explainer import build_storyboard


class HybridVideoTests(unittest.TestCase):
    def make_storyboard(self):
        return build_storyboard(
            topic="Rolling Bodies",
            objective="Relate translation, rotation, and kinetic energy on an incline.",
            narration=(
                "A rolling body translates and rotates. The no-slip condition links v and omega. "
                "Energy is shared between translation and rotation. Compare a solid cylinder and a ring."
            ),
            mastery_check="Which body reaches the bottom first and why?",
            equations=["v = ωR", "K = ½Mv² + ½Iω²"],
            learner_interest="coding and game development",
            analogy_consent=True,
            duration=15,
            derived=True,
        )

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for media integration test")
    def test_local_renderer_creates_playable_mp4(self):
        storyboard = self.make_storyboard()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rolling.mp4"
            result = render_local_cinematic(storyboard, output, fps=4)
            self.assertEqual(result.provider, "local-cinematic")
            self.assertTrue(output.exists())
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height", "-of", "json", str(output)],
                check=True, capture_output=True, text=True,
            )
            metadata = json.loads(probe.stdout)
            self.assertEqual(metadata["streams"][0]["codec_name"], "h264")
            self.assertEqual(metadata["streams"][0]["width"], 1280)
            self.assertEqual(metadata["streams"][0]["height"], 720)
            self.assertGreater(float(metadata["format"]["duration"]), 14)

    def test_hybrid_uses_hosted_adapter_only_after_local_failure(self):
        storyboard = self.make_storyboard()
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.mp4"
            result = render_hybrid(storyboard, output, hosted_renderer=lambda _storyboard, path: calls.append(path) or path)
            self.assertEqual(result.provider, "local-cinematic")
            self.assertEqual(calls, [])

    def test_manifest_is_written_for_result(self):
        storyboard = self.make_storyboard()
        with tempfile.TemporaryDirectory() as directory:
            result = render_hybrid(storyboard, Path(directory) / "result.mp4")
            manifest = render_result_manifest(result, Path(directory) / "manifest.json")
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["provider"], "local-cinematic")
            self.assertEqual(payload["aspect_ratio"], "16:9")


if __name__ == "__main__":
    unittest.main()
