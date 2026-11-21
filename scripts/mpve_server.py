#!/usr/bin/env python3
"""Run the protected local MPVE HTTP API.

Endpoints:
  POST /videos
  GET  /videos/{job_id}
  GET  /videos/{job_id}/result
  GET  /videos/{job_id}/artifact
"""
from __future__ import annotations

import argparse
import hmac
import ipaddress
import json
import os
import ssl
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.mpve_engine import JobStore, MPVEEngine


MAX_REQUEST_BYTES = 64 * 1024
DEFAULT_REQUESTS_PER_MINUTE = 120
DEFAULT_RETENTION_DAYS = 30
REQUEST_STRING_LIMITS = {
    "topic": 200,
    "objective": 2000,
    "misconception": 2000,
    "subtopic": 200,
    "learner_level": 100,
    "narration": 12000,
    "mastery_check": 2000,
    "exam_profile": 100,
    "mode": 50,
    "style": 50,
    "aspect_ratio": 16,
    "learner_interest": 200,
    "caption_direction": 10,
    "idempotency_key": 200,
    "subject": 100,
}
REQUEST_KEYS = set(REQUEST_STRING_LIMITS) | {
    "prerequisites", "duration", "analogy_consent", "derived", "caption_words"
}
NULLABLE_STRING_KEYS = {"exam_profile", "learner_interest", "idempotency_key"}


def validate_request_payload(payload: object) -> None:
    """Enforce the public JSON schema and bound individual user-controlled fields."""
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    unknown = set(payload) - REQUEST_KEYS
    if unknown:
        raise ValueError(f"unknown request fields: {', '.join(sorted(str(key) for key in unknown))}")
    for key, limit in REQUEST_STRING_LIMITS.items():
        if key not in payload:
            continue
        value = payload[key]
        if value is None and key in NULLABLE_STRING_KEYS:
            continue
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        if len(value) > limit:
            raise ValueError(f"{key} exceeds the {limit}-character limit")
    if "duration" in payload and (type(payload["duration"]) is not int):
        raise ValueError("duration must be an integer")
    for key in ("analogy_consent", "derived"):
        if key in payload and type(payload[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    prerequisites = payload.get("prerequisites", [])
    if isinstance(prerequisites, str):
        prerequisites = [prerequisites]
    if not isinstance(prerequisites, list) or len(prerequisites) > 32:
        raise ValueError("prerequisites must be a string or a list of at most 32 strings")
    if any(not isinstance(item, str) or len(item) > 200 for item in prerequisites):
        raise ValueError("each prerequisite must be a string of at most 200 characters")
    caption_words = payload.get("caption_words", [])
    if not isinstance(caption_words, list) or len(caption_words) > 5000:
        raise ValueError("caption_words must be a list containing at most 5000 entries")
    for index, word in enumerate(caption_words):
        if not isinstance(word, dict) or set(word) - {"text", "start_ms", "end_ms", "page_break_after"}:
            raise ValueError(f"caption_words[{index}] must be an object with supported fields")
        if not isinstance(word.get("text"), str) or len(word["text"]) > 200:
            raise ValueError(f"caption_words[{index}].text must be a string of at most 200 characters")
        for key in ("start_ms", "end_ms"):
            if type(word.get(key)) is not int:
                raise ValueError(f"caption_words[{index}].{key} must be an integer")
        if "page_break_after" in word and type(word["page_break_after"]) is not bool:
            raise ValueError(f"caption_words[{index}].page_break_after must be a boolean")


def public_result(job_id: str, result: dict) -> dict:
    """Remove host filesystem paths and expose the MP4 through its protected route."""
    public = dict(result)
    artifact_available = bool(public.get("artifact"))
    public["artifact"] = f"/videos/{quote(job_id, safe='')}/artifact" if artifact_available else None
    for key in ("manifest", "storyboard", "final_review"):
        value = public.pop(key, None)
        public[f"{key}_available"] = bool(value)
    fallback_assets = public.pop("fallback_assets", [])
    public["fallback_asset_count"] = len(fallback_assets) if isinstance(fallback_assets, list) else 0
    captions = public.pop("captions", None)
    public["captions"] = {
        "available": bool(captions),
        "formats": sorted(captions) if isinstance(captions, dict) else [],
    }
    qa = public.get("qa")
    if isinstance(qa, dict):
        qa = dict(qa)
        qa.pop("output_path", None)
        qa.pop("probe", None)
        frames = qa.pop("representative_frames", [])
        qa["representative_frame_count"] = len(frames) if isinstance(frames, list) else 0
        public["qa"] = qa
    return public


def public_job(job: dict) -> dict:
    """Project a persisted job into a data-minimized public response."""
    public = {key: value for key, value in job.items() if key != "request"}
    if isinstance(public.get("result"), dict):
        public["result"] = public_result(job["job_id"], public["result"])
    return public


class FixedWindowRateLimiter:
    """Small per-client-IP fixed-window limiter for a single MPVE process."""

    def __init__(self, requests_per_minute: int, window_seconds: float = 60.0):
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be at least 1")
        self.limit = requests_per_minute
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._clients: dict[str, tuple[float, int]] = {}

    def check(self, client_ip: str, *, now: float | None = None) -> tuple[bool, int]:
        current = time.monotonic() if now is None else now
        with self._lock:
            expired = [ip for ip, (started, _count) in self._clients.items() if current - started >= self.window_seconds]
            for ip in expired:
                self._clients.pop(ip, None)
            started, count = self._clients.get(client_ip, (current, 0))
            if count >= self.limit:
                return False, max(1, int(self.window_seconds - (current - started) + 0.999))
            if len(self._clients) >= 10000 and client_ip not in self._clients:
                return False, max(1, int(self.window_seconds))
            self._clients[client_ip] = (started, count + 1)
            return True, 0


def validate_bind_security(host: str, api_token: str | None, tls_enabled: bool = False) -> None:
    """Require a bearer token and TLS before listening beyond loopback."""
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host.lower() == "localhost"
    if not loopback and not api_token:
        raise ValueError("MPVE_API_TOKEN is required when binding to a non-loopback address")
    if not loopback and len(api_token) < 32:
        raise ValueError("MPVE_API_TOKEN must contain at least 32 characters for non-loopback binds")
    if not loopback and not tls_enabled:
        raise ValueError("TLS certificate and key are required when binding to a non-loopback address")


class MPVEHandler(BaseHTTPRequestHandler):
    engine: MPVEEngine
    api_token: str | None = None
    rate_limiter: FixedWindowRateLimiter
    max_request_bytes = MAX_REQUEST_BYTES

    def _send(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _guard_request(self) -> bool:
        if self.api_token:
            authorization = self.headers.get("Authorization", "")
            scheme, separator, supplied = authorization.partition(" ")
            matches = hmac.compare_digest(supplied.encode("utf-8"), self.api_token.encode("utf-8"))
            if not separator or scheme.lower() != "bearer" or not matches:
                self._send(401, {"error": "unauthorized"}, {"WWW-Authenticate": "Bearer"})
                return False
        allowed, retry_after = self.rate_limiter.check(self.client_address[0])
        if not allowed:
            self._send(429, {"error": "rate limit exceeded"}, {"Retry-After": str(retry_after)})
            return False
        return True

    def do_POST(self) -> None:
        if not self._guard_request():
            return
        if urlparse(self.path).path != "/videos":
            self._send(404, {"error": "not found"})
            return
        if self.headers.get("Transfer-Encoding"):
            self._send(400, {"error": "transfer-encoded request bodies are not supported"})
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._send(415, {"error": "Content-Type must be application/json"})
            return
        raw_length = self.headers.get("Content-Length")
        if raw_length is None or len(raw_length) > 10 or not raw_length.isdecimal():
            self._send(411, {"error": "a valid Content-Length header is required"})
            return
        size = int(raw_length)
        if size > self.max_request_bytes:
            self._send(413, {"error": f"request body exceeds {self.max_request_bytes} bytes"})
            return
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError("request body ended before Content-Length bytes were received")
            payload = json.loads(raw or b"{}")
            validate_request_payload(payload)
            job, duplicate = self.engine.submit(payload)
            self._send(200 if duplicate else 202, {"job": public_job(job), "duplicate": duplicate})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
        except Exception:
            self._send(500, {"error": "internal server error"})

    def do_GET(self) -> None:
        if not self._guard_request():
            return
        path = urlparse(self.path).path.strip("/").split("/")
        if len(path) not in (2, 3) or path[0] != "videos":
            self._send(404, {"error": "not found"})
            return
        job_id = path[1]
        try:
            job = self.engine.status(job_id)
            if len(path) == 2:
                self._send(200, {"job": public_job(job)})
                return
            if path[2] == "result":
                if job["state"] != "completed":
                    self._send(409, {"error": f"job is {job['state']}; result is not available", "job": public_job(job)})
                    return
                self._send(200, {"job": public_job(job), "result": public_result(job_id, job["result"])})
                return
            if path[2] == "artifact":
                artifact = self.engine.artifact_path(job_id)
                size = artifact.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(size))
                self.send_header("Content-Disposition", f'attachment; filename="{job_id}.mp4"')
                self.send_header("Cache-Control", "private, no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                with artifact.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        self.wfile.write(chunk)
                return
            self._send(404, {"error": "not found"})
        except KeyError:
            self._send(404, {"error": "job not found", "job_id": job_id})
        except (FileNotFoundError, OSError):
            self._send(404, {"error": "artifact not available"})
        except Exception:
            self._send(500, {"error": "internal server error"})

    def log_message(self, format: str, *args) -> None:
        return


def serve(
    host: str = "127.0.0.1",
    port: int = 8787,
    output_root: str | None = None,
    *,
    data_dir: str | None = None,
    workers: int = 1,
    api_token: str | None = None,
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
    max_request_bytes: int = MAX_REQUEST_BYTES,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    tls_certfile: str | None = None,
    tls_keyfile: str | None = None,
) -> None:
    api_token = api_token or os.environ.get("MPVE_API_TOKEN")
    if bool(tls_certfile) != bool(tls_keyfile):
        raise ValueError("TLS certificate and key must be configured together")
    validate_bind_security(host, api_token, tls_enabled=bool(tls_certfile and tls_keyfile))
    if max_request_bytes < 1:
        raise ValueError("max_request_bytes must be at least 1")
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")
    rate_limiter = FixedWindowRateLimiter(requests_per_minute)
    if output_root:
        jobs_root = Path(output_root)
        persistent_root = jobs_root.parent
    else:
        persistent_root = Path(data_dir or os.environ.get("MPVE_DATA_DIR", "build/mpve"))
        jobs_root = persistent_root / "jobs"
    persistent_root.mkdir(parents=True, exist_ok=True)
    jobs_root.mkdir(parents=True, exist_ok=True)
    store = JobStore(jobs_root, db_path=persistent_root / "mpve.sqlite3")
    engine = MPVEEngine(jobs_root, store=store, worker_count=workers, retention_days=retention_days)

    class Handler(MPVEHandler):
        pass

    Handler.engine = engine
    Handler.api_token = api_token
    Handler.rate_limiter = rate_limiter
    Handler.max_request_bytes = max_request_bytes
    try:
        server = ThreadingHTTPServer((host, port), Handler)
        if tls_certfile and tls_keyfile:
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls_context.load_cert_chain(certfile=tls_certfile, keyfile=tls_keyfile)
            server.socket = tls_context.wrap_socket(server.socket, server_side=True)
    except Exception:
        if "server" in locals():
            server.server_close()
        engine.close()
        raise
    server.daemon_threads = True
    print(
        f"MPVE listening on {'https' if tls_certfile else 'http'}://{host}:{port} (data_dir={persistent_root}, workers={workers}, retention_days={retention_days}, authentication={'enabled' if api_token else 'loopback-only'})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        engine.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--data-dir", default=os.environ.get("MPVE_DATA_DIR", "build/mpve"), help="Persistent directory for the SQLite database and video jobs")
    parser.add_argument("--output-root", help="Legacy override for the jobs directory; database is stored in its parent")
    parser.add_argument("--workers", type=int, default=int(os.environ.get("MPVE_WORKERS", "1")))
    parser.add_argument("--requests-per-minute", type=int, default=DEFAULT_REQUESTS_PER_MINUTE)
    parser.add_argument("--max-request-bytes", type=int, default=MAX_REQUEST_BYTES)
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    parser.add_argument("--tls-cert", help="TLS certificate PEM; required with --tls-key for non-loopback binds")
    parser.add_argument("--tls-key", help="TLS private-key PEM; required with --tls-cert for non-loopback binds")
    args = parser.parse_args()
    serve(
        args.host,
        args.port,
        args.output_root,
        data_dir=args.data_dir,
        workers=args.workers,
        requests_per_minute=args.requests_per_minute,
        max_request_bytes=args.max_request_bytes,
        retention_days=args.retention_days,
        tls_certfile=args.tls_cert,
        tls_keyfile=args.tls_key,
    )
