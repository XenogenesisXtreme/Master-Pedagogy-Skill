import io
import json
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from scripts.mpve_client import MPVEClient, MPVEClientError, MPVEJobFailed, MPVETimeoutError


class FakeResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class MPVEClientTests(unittest.TestCase):
    def job(self, state="queued"):
        return {"job_id": "mps-test-1", "state": state, "stage": state, "progress": 0}

    def test_submit_adds_an_idempotency_key_and_returns_job(self):
        client = MPVEClient("http://localhost:8787")
        response = {"job": self.job(), "duplicate": False}
        with patch("scripts.mpve_client.urlopen", return_value=FakeResponse(response)) as open_url:
            job = client.submit({"topic": "Floatation", "objective": "Explain buoyancy"})

        request = open_url.call_args.args[0]
        posted = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.full_url, "http://localhost:8787/videos")
        self.assertTrue(posted["idempotency_key"])
        self.assertEqual(job, response["job"])

    def test_configured_api_token_is_sent_as_bearer_authorization(self):
        client = MPVEClient("http://localhost:8787", api_token="test-secret")
        response = {"job": self.job(), "duplicate": False}
        with patch("scripts.mpve_client.urlopen", return_value=FakeResponse(response)) as open_url:
            client.submit({"topic": "Floatation", "objective": "Explain buoyancy"})
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")

    def test_retry_reuses_the_same_idempotency_key(self):
        client = MPVEClient("http://localhost:8787", retry_backoff=0)
        unavailable = HTTPError("http://localhost:8787/videos", 503, "temporary", {}, io.BytesIO(b"retry"))
        response = {"job": self.job(), "duplicate": False}
        with patch("scripts.mpve_client.urlopen", side_effect=[unavailable, FakeResponse(response)]) as open_url:
            with patch("scripts.mpve_client.time.sleep"):
                job = client.submit({"topic": "Floatation", "objective": "Explain buoyancy"})

        self.assertEqual(job["job_id"], "mps-test-1")
        requests = [call.args[0] for call in open_url.call_args_list]
        first = json.loads(requests[0].data.decode("utf-8"))
        second = json.loads(requests[1].data.decode("utf-8"))
        self.assertEqual(first, second)
        self.assertEqual(first["idempotency_key"], second["idempotency_key"])

    def test_client_error_is_not_retried(self):
        client = MPVEClient("http://localhost:8787", retry_backoff=0)
        bad_request = HTTPError("http://localhost:8787/videos", 400, "invalid", {}, io.BytesIO(b"bad payload"))
        with patch("scripts.mpve_client.urlopen", side_effect=bad_request) as open_url:
            with self.assertRaises(MPVEClientError) as caught:
                client.submit({"topic": "Floatation", "objective": "Explain buoyancy"})
        self.assertEqual(caught.exception.status_code, 400)
        self.assertEqual(open_url.call_count, 1)

    def test_status_and_result_parse_api_envelopes(self):
        client = MPVEClient("http://localhost:8787")
        job = self.job("completed")
        response = {"job": job, "result": {"artifact": "/tmp/video.mp4"}}
        with patch("scripts.mpve_client.urlopen", side_effect=[FakeResponse({"job": job}), FakeResponse(response)]) as open_url:
            self.assertEqual(client.status("mps-test-1"), job)
            self.assertEqual(client.get_result("mps-test-1"), response)
        self.assertEqual(open_url.call_args_list[0].args[0].full_url, "http://localhost:8787/videos/mps-test-1")
        self.assertEqual(open_url.call_args_list[1].args[0].full_url, "http://localhost:8787/videos/mps-test-1/result")

    def test_wait_polls_until_complete_then_fetches_result(self):
        client = MPVEClient("http://localhost:8787", job_timeout=5, poll_interval=0.01)
        completed = self.job("completed")
        result = {"job": completed, "result": {"artifact": "/tmp/video.mp4"}}
        with patch.object(client, "status", side_effect=[self.job("queued"), self.job("processing"), completed]), \
             patch.object(client, "get_result", return_value=result) as get_result, \
             patch("scripts.mpve_client.time.sleep"):
            self.assertEqual(client.wait_for_result("mps-test-1"), result)
        get_result.assert_called_once_with("mps-test-1")

    def test_wait_raises_job_failed_with_terminal_status(self):
        client = MPVEClient("http://localhost:8787")
        failed = self.job("failed") | {"error": "render failed"}
        with patch.object(client, "status", return_value=failed):
            with self.assertRaises(MPVEJobFailed) as caught:
                client.wait_for_result("mps-test-1")
        self.assertEqual(caught.exception.job, failed)
        self.assertIn("render failed", str(caught.exception))

    def test_wait_timeout_preserves_last_job_for_later_polling(self):
        client = MPVEClient("http://localhost:8787", job_timeout=0)
        queued = self.job("processing")
        with patch.object(client, "status", return_value=queued):
            with self.assertRaises(MPVETimeoutError) as caught:
                client.wait_for_result("mps-test-1")
        self.assertEqual(caught.exception.job, queued)

    def test_rejects_invalid_base_url_and_timeouts(self):
        with self.assertRaises(ValueError):
            MPVEClient("ftp://localhost:8787")
        with self.assertRaises(ValueError):
            MPVEClient("http://localhost:8787", request_timeout=0)
        with self.assertRaisesRegex(ValueError, "requires HTTPS"):
            MPVEClient("http://api.example.com:8787", api_token="secret")


if __name__ == "__main__":
    unittest.main()
