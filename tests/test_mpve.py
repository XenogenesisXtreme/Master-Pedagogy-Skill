import hashlib
import json
import sqlite3
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from scripts.hybrid_video import RenderResult
from scripts.mpve_engine import JobStore, MPVEEngine, VideoRequest


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

    @contextmanager
    def running_engine(self, output_root):
        engine = MPVEEngine(output_root)
        try:
            yield engine
        finally:
            engine.close()

    def fake_result(self, _storyboard, output, **_kwargs):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"not-a-real-video-in-unit-test")
        return RenderResult("local-cinematic", output, 15, "16:9", False, [], [], ["storyboard validation"])

    def test_rejects_missing_objective(self):
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
            with self.assertRaisesRegex(ValueError, "objective is required"):
                engine.submit({"topic": "Floatation"})

    def test_rejects_fhp_before_derivation(self):
        payload = self.payload() | {"mode": "fhp"}
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
            with self.assertRaisesRegex(ValueError, "derived=true"):
                engine.submit(payload)

    def test_duplicate_requests_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
            qa = {"status": "pass", "errors": [], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 15}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value=qa):
                first, duplicate_first = engine.submit(self.payload())
                second, duplicate_second = engine.submit(self.payload())
                self.assertFalse(duplicate_first)
                self.assertTrue(duplicate_second)
                self.assertEqual(first["job_id"], second["job_id"])
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(first["job_id"])["state"] != "completed":
                    time.sleep(0.01)
                self.assertEqual(engine.status(first["job_id"])["state"], "completed")

    def test_idempotency_key_rejects_a_different_request(self):
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
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
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
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
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
            qa = {"status": "fail", "errors": ["ffprobe could not decode the output"], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 0}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value=qa):
                job, _ = engine.submit(self.payload())
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(job["job_id"])["state"] not in {"completed", "failed"}:
                    time.sleep(0.01)
                current = engine.status(job["job_id"])
                self.assertEqual(current["state"], "failed")
                self.assertIn("ffprobe", current["error"])

    def test_caption_words_create_sidecars(self):
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
            payload = self.payload() | {"caption_words": [{"text": "Floatation", "start_ms": 0, "end_ms": 800}, {"text": "explained", "start_ms": 800, "end_ms": 1500}]}
            qa = {"status": "pass", "errors": [], "warnings": [], "representative_frames": [], "audio_streams": [], "duration_seconds": 15}
            with patch("scripts.mpve_engine.render_hybrid", side_effect=self.fake_result), patch("scripts.mpve_engine.inspect_media", return_value=qa):
                job, _ = engine.submit(payload)
                deadline = time.time() + 3
                while time.time() < deadline and engine.status(job["job_id"])["state"] not in {"completed", "failed"}:
                    time.sleep(0.01)
                current = engine.status(job["job_id"])
                self.assertEqual(current["state"], "completed")
                self.assertTrue(Path(current["result"]["captions"]["vtt"]).exists())

    def test_renderer_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
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
        with tempfile.TemporaryDirectory() as directory, self.running_engine(directory) as engine:
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

    def test_job_state_and_idempotency_survive_store_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            request = VideoRequest.from_dict(self.payload() | {"idempotency_key": "persist-1"})
            first_store = JobStore(root)
            original, duplicate = first_store.create(request)
            self.assertFalse(duplicate)
            first_store.update(original["job_id"], state="processing", stage="rendering", progress=45)

            reopened_store = JobStore(root)
            persisted = reopened_store.get(original["job_id"])
            self.assertEqual(persisted["state"], "processing")
            self.assertEqual(persisted["progress"], 45)
            replay, is_duplicate = reopened_store.create(request)
            self.assertTrue(is_duplicate)
            self.assertEqual(replay["job_id"], original["job_id"])

    def test_idempotency_key_is_hashed_at_rest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            raw_key = "learner-private-token"
            store = JobStore(root)
            job, _ = store.create(VideoRequest.from_dict(self.payload() | {"idempotency_key": raw_key}))
            digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
            with sqlite3.connect(root / "mpve.sqlite3") as connection:
                mapped_key = connection.execute("SELECT idempotency_key FROM idempotency_keys").fetchone()[0]
                job_key = connection.execute("SELECT idempotency_key FROM jobs WHERE job_id = ?", (job["job_id"],)).fetchone()[0]
            self.assertEqual(mapped_key, digest)
            self.assertEqual(job_key, digest)
            self.assertNotIn(raw_key, (root / job["job_id"] / "job.json").read_text(encoding="utf-8"))

    def test_legacy_plaintext_idempotency_mapping_migrates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            raw_key = "legacy-client-key"
            request = VideoRequest.from_dict(self.payload() | {"idempotency_key": raw_key})
            store = JobStore(root)
            original, _ = store.create(request)
            digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
            with sqlite3.connect(root / "mpve.sqlite3") as connection:
                connection.execute("UPDATE idempotency_keys SET idempotency_key = ?", (raw_key,))
                connection.execute("UPDATE jobs SET idempotency_key = ? WHERE job_id = ?", (raw_key, original["job_id"]))
                connection.execute("PRAGMA user_version = 0")

            migrated = JobStore(root)
            with sqlite3.connect(root / "mpve.sqlite3") as connection:
                mapped_key = connection.execute("SELECT idempotency_key FROM idempotency_keys").fetchone()[0]
            self.assertEqual(mapped_key, digest)
            replay, duplicate = migrated.create(request)
            self.assertTrue(duplicate)
            self.assertEqual(replay["job_id"], original["job_id"])

    def test_failed_idempotent_job_can_be_retried_after_store_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            request = VideoRequest.from_dict(self.payload() | {"idempotency_key": "persist-retry"})
            first_store = JobStore(root)
            failed, _ = first_store.create(request)
            first_store.update(failed["job_id"], state="failed", stage="failed", error="renderer failed")
            self.assertNotIn("request", first_store.get(failed["job_id"]))

            reopened_store = JobStore(root)
            retried, duplicate = reopened_store.create(request)
            self.assertFalse(duplicate)
            self.assertNotEqual(retried["job_id"], failed["job_id"])
            replay, is_duplicate = reopened_store.create(request)
            self.assertTrue(is_duplicate)
            self.assertEqual(replay["job_id"], retried["job_id"])

    def test_retention_purges_terminal_job_data_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            store = JobStore(root)
            completed_request = VideoRequest.from_dict(self.payload() | {"subtopic": "expired"})
            completed, _ = store.create(completed_request)
            store.update(completed["job_id"], state="completed", result={"artifact": str(root / completed["job_id"] / "video.mp4")})
            artifact = root / completed["job_id"] / "video.mp4"
            artifact.write_bytes(b"expired test artifact")
            queued, _ = store.create(VideoRequest.from_dict(self.payload() | {"subtopic": "still queued"}))

            removed = store.purge_expired(1, now=time.time() + 10)

            self.assertEqual(removed, 1)
            self.assertIsNone(store.get(completed["job_id"]))
            self.assertFalse(artifact.parent.exists())
            self.assertEqual(store.get(queued["job_id"])["state"], "queued")
            retried, duplicate = store.create(completed_request)
            self.assertFalse(duplicate)
            self.assertNotEqual(retried["job_id"], completed["job_id"])

    def test_startup_redacts_legacy_terminal_request_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            store = JobStore(root)
            request = VideoRequest.from_dict(self.payload() | {"learner_level": "private cohort"})
            job, _ = store.create(request)
            store.update(job["job_id"], state="completed", result={"artifact": None})
            legacy = store.get(job["job_id"])
            legacy["request"] = request.canonical()
            with sqlite3.connect(root / "mpve.sqlite3") as connection:
                connection.execute(
                    "UPDATE jobs SET job_json = ? WHERE job_id = ?",
                    (json.dumps(legacy), job["job_id"]),
                )
            store._write(legacy)

            engine = MPVEEngine(root, store=JobStore(root), start_workers=False)
            try:
                persisted = engine.status(job["job_id"])
                self.assertNotIn("request", persisted)
                mirror = (root / job["job_id"] / "job.json").read_text(encoding="utf-8")
                self.assertNotIn("private cohort", mirror)
            finally:
                engine.close()

    def test_artifact_path_is_confined_to_completed_job_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            engine = MPVEEngine(root, start_workers=False)
            try:
                job, _ = engine.store.create(VideoRequest.from_dict(self.payload()))
                artifact = root / job["job_id"] / "video.mp4"
                artifact.write_bytes(b"valid test fixture")
                engine.store.update(job["job_id"], state="completed", result={"artifact": str(artifact)})
                self.assertEqual(engine.artifact_path(job["job_id"]), artifact.resolve())

                outside = Path(directory) / "outside.mp4"
                outside.write_bytes(b"must not be served")
                engine.store.update(job["job_id"], result={"artifact": str(outside)})
                with self.assertRaises(FileNotFoundError):
                    engine.artifact_path(job["job_id"])
            finally:
                engine.close()

    def test_engine_requeues_interrupted_job_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            store = JobStore(root)
            interrupted, _ = store.create(VideoRequest.from_dict(self.payload()))
            store.update(interrupted["job_id"], state="processing", stage="rendering", progress=45)

            restarted = MPVEEngine(root, store=JobStore(root), start_workers=False)
            try:
                recovered = restarted.status(interrupted["job_id"])
                self.assertEqual(recovered["state"], "queued")
                self.assertEqual(recovered["stage"], "queued")
                self.assertEqual(recovered["progress"], 0)
            finally:
                restarted.close()

    def test_durable_queue_claims_each_job_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "jobs"
            store = JobStore(root)
            queued_jobs = [
                store.create(VideoRequest.from_dict(self.payload() | {"subtopic": f"case-{index}"}))[0]
                for index in range(6)
            ]

            independent_stores = [JobStore(root) for _ in range(6)]
            with ThreadPoolExecutor(max_workers=6) as executor:
                claims = list(executor.map(lambda independent_store: independent_store.claim_next(), independent_stores))

            claimed_ids = [claim["job_id"] for claim in claims if claim]
            self.assertEqual(set(claimed_ids), {job["job_id"] for job in queued_jobs})
            self.assertEqual(len(claimed_ids), len(set(claimed_ids)))
            self.assertTrue(all(claim["state"] == "processing" for claim in claims))
            self.assertIsNone(store.claim_next())


if __name__ == "__main__":
    unittest.main()
