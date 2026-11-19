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

    def test_idempotency_key_rejects_a_different_request(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            payload = self.payload() | {"idempotency_key": "request-1"}
            qa = {"status": "pass", "errors": [], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 15}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value=qa):
                first, _ = engine.submit(payload)
                with self.assertRaisesRegex(ValueError, "different request"):
                    engine.submit(payload | {"objective": "A different objective."})
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(first["job_id"])["state"] != "completed":
                    time.sleep(0.01)
                self.assertEqual(engine.status(first["job_id"])["state"], "completed")

    def test_successful_job_has_result_and_storyboard(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            qa = {"status": "pass", "errors": [], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 15}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value=qa):
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

    def test_invalid_media_is_not_marked_completed(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            qa = {"status": "fail", "errors": ["ffprobe could not decode the output"], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 0}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value=qa):
                job, _ = engine.submit(self.payload())
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(job["job_id"])["state"] == "processing":
                    time.sleep(0.01)
                current = engine.status(job["job_id"])
                self.assertEqual(current["state"], "failed")
                self.assertIn("ffprobe", current["error"])

    def test_caption_words_create_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            payload = self.payload() | {"caption_words": [{"text": "Floatation", "start_ms": 0, "end_ms": 800}, {"text": "explained", "start_ms": 800, "end_ms": 1500}]}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value={"status": "pass", "errors": [], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 15}):
                job, _ = engine.submit(payload)
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(job["job_id"])["state"] == "processing":
                    time.sleep(0.01)
                current = engine.status(job["job_id"])
                self.assertEqual(current["state"], "completed")
                self.assertTrue(Path(current["result"]["captions"]["vtt"]).exists())

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

    def test_failed_request_can_be_retried_with_same_idempotency_key(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MPVEEngine(directory)
            payload = self.payload() | {"idempotency_key": "retry-1"}
            render_calls = 0
            qa = {"status": "pass", "errors": [], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 15}

            def fail_once_then_succeed(storyboard, output, **kwargs):
                nonlocal render_calls
                render_calls += 1
                if render_calls == 1:
                    raise RuntimeError("temporary ffmpeg failure")
                return self.fake_result(storyboard, output, **kwargs)

            with patch("scripts.mpve_engine.render_hybrid", side_effect=fail_once_then_succeed), patch("scripts.mpve_engine.inspect_media", return_value=qa):
                first, duplicate_first = engine.submit(payload)
                self.assertFalse(duplicate_first)
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(first["job_id"])["state"] != "failed":
                    time.sleep(0.01)
                self.assertEqual(engine.status(first["job_id"])["state"], "failed")

                retry, duplicate_retry = engine.submit(payload)
                self.assertFalse(duplicate_retry)
                self.assertNotEqual(first["job_id"], retry["job_id"])
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(retry["job_id"])["state"] != "completed":
                    time.sleep(0.01)
                self.assertEqual(engine.status(retry["job_id"])["state"], "completed")
                self.assertEqual(render_calls, 2)

                duplicate, is_duplicate = engine.submit(payload)
                self.assertTrue(is_duplicate)
                self.assertEqual(duplicate["job_id"], retry["job_id"])


if __name__ == "__main__":
    unittest.main()
