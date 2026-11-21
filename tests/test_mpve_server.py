import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from scripts.mpve_server import FixedWindowRateLimiter, MPVEHandler, validate_bind_security


class FakeEngine:
    def __init__(self, artifact: Path):
        self.artifact = artifact
        self.submitted = None

    def submit(self, payload):
        self.submitted = payload
        return {
            "job_id": "mps-test123abc",
            "state": "queued",
            "stage": "queued",
            "progress": 0,
            "request": payload,
        }, False

    def status(self, job_id):
        if job_id != "mps-test123abc":
            raise KeyError(job_id)
        return {
            "job_id": job_id,
            "state": "completed",
            "request": {"learner_level": "private learner context"},
            "result": {
                "artifact": str(self.artifact),
                "manifest": str(self.artifact.parent / "manifest.json"),
                "storyboard": str(self.artifact.parent / "storyboard.json"),
                "final_review": str(self.artifact.parent / "review.json"),
                "fallback_assets": [],
                "captions": None,
                "qa": {
                    "status": "pass",
                    "output_path": str(self.artifact),
                    "probe": {"format": {"filename": str(self.artifact)}},
                    "representative_frames": [str(self.artifact.parent / "frame.jpg")],
                },
            },
        }

    def artifact_path(self, job_id):
        if job_id != "mps-test123abc":
            raise FileNotFoundError(job_id)
        return self.artifact


class MPVEServerSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifact = self.root / "video.mp4"
        self.artifact.write_bytes(b"safe video bytes")
        self.engine = FakeEngine(self.artifact)
        self.server = None
        self.thread = None

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=3)
        self.temp.cleanup()

    def start_server(self, *, token=None, rate=120, max_request_bytes=64 * 1024):
        handler = type("TestMPVEHandler", (MPVEHandler,), {})
        handler.engine = self.engine
        handler.api_token = token
        handler.rate_limiter = FixedWindowRateLimiter(rate)
        handler.max_request_bytes = max_request_bytes
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def request(self, method, path, *, payload=None, token=None, raw_body=None):
        body = raw_body
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if method == "POST":
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, response.headers, response.read()
        except HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_non_loopback_requires_token_and_tls(self):
        validate_bind_security("127.0.0.1", None)
        validate_bind_security("localhost", None)
        with self.assertRaisesRegex(ValueError, "MPVE_API_TOKEN"):
            validate_bind_security("0.0.0.0", None, tls_enabled=True)
        with self.assertRaisesRegex(ValueError, "32 characters"):
            validate_bind_security("0.0.0.0", "short-token", tls_enabled=True)
        with self.assertRaisesRegex(ValueError, "TLS"):
            validate_bind_security("0.0.0.0", "x" * 32, tls_enabled=False)
        validate_bind_security("0.0.0.0", "x" * 32, tls_enabled=True)

    def test_bearer_token_is_required_and_public_job_omits_request(self):
        self.start_server(token="secret-token")
        status, headers, body = self.request("GET", "/videos/mps-test123abc")
        self.assertEqual(status, 401)
        self.assertEqual(headers.get("WWW-Authenticate"), "Bearer")

        status, _headers, body = self.request(
            "POST",
            "/videos",
            token="secret-token",
            payload={"topic": "Floatation", "objective": "Explain buoyancy", "learner_level": "private"},
        )
        self.assertEqual(status, 202)
        response = json.loads(body)
        self.assertNotIn("request", response["job"])
        self.assertNotIn("private", body.decode("utf-8"))
        self.assertEqual(self.engine.submitted["topic"], "Floatation")

    def test_rate_limit_returns_retry_after(self):
        self.start_server(rate=1)
        first, _headers, _body = self.request("GET", "/videos/mps-test123abc")
        second, headers, body = self.request("GET", "/videos/mps-test123abc")
        self.assertEqual(first, 200)
        self.assertEqual(second, 429)
        self.assertGreaterEqual(int(headers["Retry-After"]), 1)
        self.assertIn("rate limit", json.loads(body)["error"])

    def test_request_body_limit_and_schema_are_enforced(self):
        self.start_server(max_request_bytes=256)
        oversized, _headers, _body = self.request("POST", "/videos", raw_body=b"{" + b" " * 300 + b"}")
        self.assertEqual(oversized, 413)

        invalid, _headers, body = self.request(
            "POST", "/videos", payload={"topic": "Floatation", "objective": "Explain buoyancy", "extra": "not allowed"}
        )
        self.assertEqual(invalid, 400)
        self.assertIn("unknown request fields", json.loads(body)["error"])

    def test_result_hides_disk_paths_and_artifact_download_is_protected(self):
        self.start_server(token="secret-token")
        status, _headers, _body = self.request("GET", "/videos/mps-test123abc/result")
        self.assertEqual(status, 401)

        status, _headers, body = self.request("GET", "/videos/mps-test123abc/result", token="secret-token")
        self.assertEqual(status, 200)
        decoded = json.loads(body)
        self.assertEqual(decoded["result"]["artifact"], "/videos/mps-test123abc/artifact")
        self.assertNotIn(str(self.root), body.decode("utf-8"))
        self.assertNotIn("private learner context", body.decode("utf-8"))

        status, headers, body = self.request("GET", "/videos/mps-test123abc/artifact", token="secret-token")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get_content_type(), "video/mp4")
        self.assertEqual(body, b"safe video bytes")


if __name__ == "__main__":
    unittest.main()
