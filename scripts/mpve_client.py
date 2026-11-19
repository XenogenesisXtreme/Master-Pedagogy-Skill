#!/usr/bin/env python3
"""Small, retry-safe HTTP client for the MPVE API."""
from __future__ import annotations

import json
import time
import uuid
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


class MPVEClientError(RuntimeError):
    """An HTTP, transport, or response-contract error from MPVE."""

    def __init__(self, message: str, *, status_code: int | None = None, response_body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class MPVEJobFailed(MPVEClientError):
    """Raised when MPVE reports a terminal failed job."""

    def __init__(self, job: dict[str, Any]):
        self.job = job
        job_id = job.get("job_id", "unknown")
        reason = job.get("error") or "no error details were returned"
        super().__init__(f"MPVE job {job_id} failed: {reason}")


class MPVETimeoutError(MPVEClientError):
    """Raised when bounded polling expires while a job is still active."""

    def __init__(self, job: dict[str, Any]):
        self.job = job
        job_id = job.get("job_id", "unknown")
        state = job.get("state", "unknown")
        super().__init__(f"Timed out waiting for MPVE job {job_id}; last state was {state}")


class MPVEClient:
    """HTTP adapter for submit, poll, and result operations.

    The standard library is used so the MPS host can inject ``client.submit``
    into ``MPSRecoveryOrchestrator`` without adding a runtime dependency.
    Network retries are bounded; submission retries reuse one idempotency key.
    """

    _JOB_STATES = {"queued", "processing", "completed", "failed"}
    _RETRYABLE_HTTP = {408, 425, 429}

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8787",
        *,
        request_timeout: float = 10.0,
        job_timeout: float = 600.0,
        poll_interval: float = 1.0,
        max_retries: int = 2,
        retry_backoff: float = 0.25,
        max_retry_backoff: float = 2.0,
    ):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("base_url must be an HTTP(S) origin or path without query/fragment")
        if request_timeout <= 0 or job_timeout < 0 or poll_interval <= 0:
            raise ValueError("request_timeout and poll_interval must be positive; job_timeout cannot be negative")
        if max_retries < 0 or retry_backoff < 0 or max_retry_backoff < 0:
            raise ValueError("retry limits and backoff values cannot be negative")
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout
        self.job_timeout = job_timeout
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.max_retry_backoff = max_retry_backoff

    def submit(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Submit a request and return its job; safe to inject as submit_video."""
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")
        body = dict(payload)
        key = body.get("idempotency_key")
        if key is None:
            key = uuid.uuid4().hex
        elif not isinstance(key, str) or not key.strip():
            raise ValueError("idempotency_key must be a non-empty string")
        body["idempotency_key"] = key
        response = self._request_json("POST", "/videos", body)
        return self._extract_job(response, "submit")

    def status(self, job_id: str) -> dict[str, Any]:
        """Fetch a job's latest state."""
        response = self._request_json("GET", f"/videos/{self._quoted_job_id(job_id)}")
        return self._extract_job(response, "status")

    def get_result(self, job_id: str) -> dict[str, Any]:
        """Fetch a completed job and its result payload."""
        response = self._request_json("GET", f"/videos/{self._quoted_job_id(job_id)}/result")
        if not isinstance(response.get("job"), dict) or not isinstance(response.get("result"), dict):
            raise MPVEClientError("MPVE result response must contain job and result objects")
        return response

    def wait_for_result(
        self,
        job_id: str,
        *,
        timeout_seconds: float | None = None,
        poll_interval_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Poll until completion, failure, or a bounded timeout.

        A timeout is not treated as a failed render: callers may resume polling
        later using the returned last job in ``MPVETimeoutError.job``.
        """
        timeout = self.job_timeout if timeout_seconds is None else timeout_seconds
        interval = self.poll_interval if poll_interval_seconds is None else poll_interval_seconds
        if timeout < 0 or interval <= 0:
            raise ValueError("timeout_seconds cannot be negative and poll_interval_seconds must be positive")
        deadline = time.monotonic() + timeout
        while True:
            job = self.status(job_id)
            state = job.get("state")
            if state == "failed":
                raise MPVEJobFailed(job)
            if state == "completed":
                return self.get_result(job_id)
            if state not in {"queued", "processing"}:
                raise MPVEClientError(f"MPVE returned an unknown job state: {state!r}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MPVETimeoutError(job)
            time.sleep(min(interval, remaining))

    @staticmethod
    def _quoted_job_id(job_id: str) -> str:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string")
        return quote(job_id, safe="")

    @staticmethod
    def _extract_job(response: dict[str, Any], operation: str) -> dict[str, Any]:
        job = response.get("job")
        if not isinstance(job, dict) or not job.get("job_id"):
            raise MPVEClientError(f"MPVE {operation} response did not contain a job")
        state = job.get("state")
        if state not in MPVEClient._JOB_STATES:
            raise MPVEClientError(f"MPVE {operation} response contained an unknown job state: {state!r}")
        return job

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=data, headers=headers, method=method)

        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.request_timeout) as response:
                    raw = response.read()
                decoded = json.loads(raw.decode("utf-8"))
                if not isinstance(decoded, dict):
                    raise MPVEClientError("MPVE returned a JSON value that was not an object")
                return decoded
            except HTTPError as exc:
                raw = exc.read()
                body = raw.decode("utf-8", errors="replace")
                retryable = exc.code in self._RETRYABLE_HTTP or 500 <= exc.code <= 599
                if retryable and attempt < self.max_retries:
                    self._sleep_before_retry(attempt, getattr(exc, "headers", None))
                    continue
                detail = body[:1000] or str(exc.reason)
                raise MPVEClientError(
                    f"MPVE returned HTTP {exc.code} for {method} {path}: {detail}",
                    status_code=exc.code,
                    response_body=body,
                ) from exc
            except (URLError, TimeoutError, ConnectionError, OSError) as exc:
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise MPVEClientError(
                    f"MPVE request {method} {path} failed after {attempt + 1} attempt(s): {exc}"
                ) from exc
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MPVEClientError(f"MPVE returned invalid JSON for {method} {path}") from exc
        raise AssertionError("bounded retry loop exited unexpectedly")

    def _sleep_before_retry(self, attempt: int, headers: Any = None) -> None:
        delay = min(self.retry_backoff * (2**attempt), self.max_retry_backoff)
        retry_after = headers.get("Retry-After") if headers is not None else None
        if retry_after is not None:
            try:
                delay = min(max(float(retry_after), 0.0), self.max_retry_backoff)
            except (TypeError, ValueError):
                pass
        if delay:
            time.sleep(delay)
