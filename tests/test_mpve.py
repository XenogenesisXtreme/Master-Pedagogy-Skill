import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.hybrid_video import RenderResult
from scripts.mpve_engine import MPVEEngine


class MPVETests(unittest.TestCase):
    def payload(self):
        return {
            "topic": "Floatation",
            "objective": "Explain why buoyant force can balance weight.",
            "misconception": "A heavier object must always sink.",
            "mastery_check": "State the condition for equilibrium.",
            "duration": 15,
            "aspect_ratio": "16:9",
            "style": "cinematic",
        }

    def fake_result(self, _storyboard, output, **_kwargs):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"not-a-real-video-in-unit-test")
        return RenderResult("local-cinematic", output, 15, "16:9", False, [], [], ["storyboard validation"])

    def test_rejects_missing_objective(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "objective is required"):
                MPVEEngine(directory).submit({"topic": "Floatation"})

    def test_rejects_fhp_before_derivation(self):
        payload = self.payload() | {"mode": "fhp"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "derived=true"):
                MPVEEngine(directory).submit(payload)

    def test_duplicate_requests_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result):
                first, duplicate_first = engine.submit(self.payload())
                second, duplicate_second = engine.submit(self.payload())
                self.assertFalse(duplicate_first)
                self.assertTrue(duplicate_second)
                self.assertEqual(first["job_id"], second["job_id"])

    def test_successful_job_has_result_and_storyboard(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result):
                job, _ = engine.submit(self.payload())
                deadline = time.time() + 3
                while time.time() < deadline:
                    current = engine.status(job["job_id"])
                    if current["state"] == "completed":
                        break
                    time.sleep(0.01)
                current = engine.status(job["job_id"])
                self.assertEqual(current["state"], "completed")
                self.assertTrue(Path(current["result"]["storyboard"]).exists())
                self.assertTrue(current["result"]["artifact"].endswith("video.mp4"))

    def test_renderer_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            with patch("scripts.mpve_engine.render_hybrid", side_effect=RuntimeError("ffmpeg unavailable")):
                job, _ = engine.submit(self.payload())
                deadline = time.time() + 3
                while time.time() < deadline:
                    current = engine.status(job["job_id"])
                    if current["state"] == "failed":
                        break
                    time.sleep(0.01)
                current = engine.status(job["job_id"])
                self.assertEqual(current["state"], "failed")
                self.assertIn("ffmpeg unavailable", current["error"])


if __name__ == "__main__":
    unittest.main()
