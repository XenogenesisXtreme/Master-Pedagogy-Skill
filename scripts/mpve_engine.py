#!/usr/bin/env python3
"""Master Pedagogy Video Engine: a small, provider-neutral vertical slice.

MPS decides whether a video is appropriate and supplies learning context. MPVE
plans and renders the requested intervention, persists job state, and returns
artifacts and QA metadata. The implementation is intentionally independent of
OpenMontage source code.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.hybrid_video import render_hybrid, render_result_manifest
from scripts.mpve_captions import CaptionWord, write_sidecars
from scripts.mpve_qa import inspect_media, write_final_review
from scripts.video_explainer import MAX_DURATION_SECONDS, MIN_DURATION_SECONDS, build_storyboard

JOB_STATES = {"queued", "processing", "completed", "failed"}


@dataclass
class VideoRequest:
    topic: str
    objective: str
    misconception: str = ""
    subtopic: str = ""
    learner_level: str = ""
    prerequisites: tuple[str, ...] = ()
    narration: str = ""
    mastery_check: str = "Explain the result in your own words."
    exam_profile: str | None = None
    mode: str = "standard"
    style: str = "cinematic"
    duration: int = 15
    aspect_ratio: str = "16:9"
    learner_interest: str | None = None
    analogy_consent: bool = False
    derived: bool = False
    caption_words: tuple[dict[str, Any], ...] = ()
    caption_direction: str = "auto"
    idempotency_key: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VideoRequest":
        prerequisites = payload.get("prerequisites", ())
        if isinstance(prerequisites, str):
            prerequisites = (prerequisites,)
        return cls(
            topic=str(payload.get("topic", "")).strip(),
            objective=str(payload.get("objective", "")).strip(),
            misconception=str(payload.get("misconception", "")).strip(),
            subtopic=str(payload.get("subtopic", "")).strip(),
            learner_level=str(payload.get("learner_level", "")).strip(),
            prerequisites=tuple(str(item).strip() for item in prerequisites if str(item).strip()),
            narration=str(payload.get("narration", "")).strip(),
            mastery_check=str(payload.get("mastery_check", cls.mastery_check)).strip(),
            exam_profile=payload.get("exam_profile"),
            mode=str(payload.get("mode", "standard")),
            style=str(payload.get("style", "cinematic")),
            duration=int(payload.get("duration", 15)),
            aspect_ratio=str(payload.get("aspect_ratio", "16:9")),
            learner_interest=payload.get("learner_interest"),
            analogy_consent=bool(payload.get("analogy_consent", False)),
            derived=bool(payload.get("derived", False)),
            caption_words=tuple(dict(word) for word in payload.get("caption_words", ()) if isinstance(word, dict)),
            caption_direction=str(payload.get("caption_direction", "auto")),
            idempotency_key=payload.get("idempotency_key"),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.topic:
            errors.append("topic is required")
        if not self.objective:
            errors.append("objective is required")
        if self.duration < MIN_DURATION_SECONDS or self.duration > MAX_DURATION_SECONDS:
            errors.append(f"duration must be between {MIN_DURATION_SECONDS} and {MAX_DURATION_SECONDS} seconds")
        if self.idempotency_key is not None and (
            not isinstance(self.idempotency_key, str) or not self.idempotency_key.strip()
        ):
            errors.append("idempotency_key must be a non-empty string")
        if self.aspect_ratio != "16:9":
            errors.append("aspect_ratio must be 16:9")
        if self.analogy_consent and not self.learner_interest:
            errors.append("learner_interest is required when analogy_consent is true")
        if self.mode.lower() in {"fhp", "floathead", "floathead physics"} and not self.derived:
            errors.append("FHP requests require derived=true after the written derivation is complete")
        if self.caption_direction not in {"auto", "ltr", "rtl"}:
            errors.append("caption_direction must be auto, ltr, or rtl")
        if self.caption_words:
            words = [CaptionWord(str(item.get("text", "")), int(item.get("start_ms", -1)), int(item.get("end_ms", -1)), bool(item.get("page_break_after", False))) for item in self.caption_words]
            from scripts.mpve_captions import validate_words
            errors.extend(validate_words(words))
        return errors

    def canonical(self) -> dict[str, Any]:
        data = asdict(self)
        data["prerequisites"] = list(self.prerequisites)
        data["caption_words"] = list(self.caption_words)
        data.pop("idempotency_key", None)
        return data

    def fingerprint(self) -> str:
        encoded = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def _default_narration(request: VideoRequest) -> str:
    misconception = f" A common misconception is: {request.misconception}." if request.misconception else ""
    subtopic = f" Focus on {request.subtopic}." if request.subtopic else ""
    return (
        f"Observe {request.topic}.{subtopic}{misconception} "
        f"The goal is to {request.objective.lower().rstrip('.')}. "
        "Define the important quantities, connect the visual relationships, and check the result. "
        f"Now test yourself: {request.mastery_check}"
    )


def _hydrostatic_narration(request: VideoRequest) -> str:
    analogy = " Think of it like debugging a game system: each added layer contributes another input to the total, but the model still needs its assumptions." if request.analogy_consent and request.learner_interest else ""
    return (
        "Imagine a thin horizontal slab of fluid at depth h. Why does its lower face feel more pressure than its upper face? "
        "Pressure is force per area, so compare the forces on the slab. The extra downward force comes from the weight of the fluid column above it. "
        "That column has volume A h, mass rho A h, and weight rho A h g. Divide its weight by area A: delta P equals rho g h. "
        "Add the pressure at the surface, P naught, and the result is P equals P naught plus rho g h. "
        "P naught is surface pressure, rho is fluid density, g is gravitational acceleration, and h is depth. "
        "Double the depth and the added pressure doubles, assuming a static uniform fluid." + analogy + " "
        "Now predict the pressure change at twice the depth."
    )


def plan_storyboard(request: VideoRequest):
    topic_lower = request.topic.lower()
    is_hydrostatic = "hydrostatic" in topic_lower or ("pressure" in topic_lower and "depth" in topic_lower)
    narration = request.narration or (_hydrostatic_narration(request) if is_hydrostatic else _default_narration(request))
    equations = []
    if request.topic.lower().find("force") >= 0:
        equations.append("F = ma")
    if is_hydrostatic:
        equations.extend(["ΔP = F/A", "m = ρAh", "F = mg = ρAhg", "ΔP = ρgh", "P = P₀ + ρgh"])
    return build_storyboard(
        topic=request.topic,
        objective=request.objective,
        narration=narration,
        mastery_check=request.mastery_check,
        exam_profile=request.exam_profile,
        mode=request.mode,
        style=request.style,
        aspect_ratio=request.aspect_ratio,
        equations=equations,
        learner_interest=request.learner_interest,
        analogy_consent=request.analogy_consent,
        duration=request.duration,
        derived=request.derived,
    )


class JobStore:
    """SQLite-backed job registry and durable queue; job folders hold artifacts."""

    def __init__(self, root: str | Path, db_path: str | Path | None = None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.root / "mpve.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    request_fingerprint TEXT NOT NULL,
                    idempotency_key TEXT,
                    state TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    job_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS jobs_state_created
                    ON jobs(state, created_at, job_id);
                CREATE TABLE IF NOT EXISTS fingerprints (
                    request_fingerprint TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id)
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    idempotency_key TEXT PRIMARY KEY,
                    request_fingerprint TEXT NOT NULL,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id)
                );
                """
            )

    @staticmethod
    def _load_job(connection: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
        row = connection.execute("SELECT job_json FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return json.loads(row["job_json"]) if row else None

    def create(self, request: VideoRequest) -> tuple[dict[str, Any], bool]:
        fingerprint = request.fingerprint()
        idempotency_key = request.idempotency_key
        with self._lock, closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if idempotency_key:
                    prior = connection.execute(
                        """SELECT i.request_fingerprint, i.job_id, j.state
                           FROM idempotency_keys AS i JOIN jobs AS j ON j.job_id = i.job_id
                           WHERE i.idempotency_key = ?""",
                        (idempotency_key,),
                    ).fetchone()
                    if prior:
                        if prior["request_fingerprint"] != fingerprint:
                            raise ValueError("idempotency_key has already been used with a different request")
                        if prior["state"] != "failed":
                            job = self._load_job(connection, prior["job_id"])
                            connection.commit()
                            return job, True

                existing = connection.execute(
                    """SELECT f.job_id, j.state FROM fingerprints AS f
                       JOIN jobs AS j ON j.job_id = f.job_id
                       WHERE f.request_fingerprint = ?""",
                    (fingerprint,),
                ).fetchone()
                if existing and existing["state"] != "failed":
                    job = self._load_job(connection, existing["job_id"])
                    if idempotency_key:
                        connection.execute(
                            """INSERT INTO idempotency_keys(idempotency_key, request_fingerprint, job_id)
                               VALUES (?, ?, ?) ON CONFLICT(idempotency_key) DO UPDATE SET
                               request_fingerprint=excluded.request_fingerprint, job_id=excluded.job_id""",
                            (idempotency_key, fingerprint, existing["job_id"]),
                        )
                    connection.commit()
                    return job, True

                now = time.time()
                job_id = f"mps-{uuid.uuid4().hex[:12]}"
                job = {
                    "job_id": job_id,
                    "state": "queued",
                    "stage": "queued",
                    "progress": 0,
                    "request": request.canonical(),
                    "request_fingerprint": fingerprint,
                    "created_at": now,
                    "updated_at": now,
                    "error": None,
                    "result": None,
                }
                connection.execute(
                    """INSERT INTO jobs(job_id, request_fingerprint, idempotency_key, state,
                       created_at, updated_at, job_json) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (job_id, fingerprint, idempotency_key, "queued", now, now, json.dumps(job, ensure_ascii=False)),
                )
                connection.execute(
                    """INSERT INTO fingerprints(request_fingerprint, job_id) VALUES (?, ?)
                       ON CONFLICT(request_fingerprint) DO UPDATE SET job_id=excluded.job_id""",
                    (fingerprint, job_id),
                )
                if idempotency_key:
                    connection.execute(
                        """INSERT INTO idempotency_keys(idempotency_key, request_fingerprint, job_id)
                           VALUES (?, ?, ?) ON CONFLICT(idempotency_key) DO UPDATE SET
                           request_fingerprint=excluded.request_fingerprint, job_id=excluded.job_id""",
                        (idempotency_key, fingerprint, job_id),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            self._write(job)
            return job, False

    def get(self, job_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            return self._load_job(connection, job_id)

    def update(self, job_id: str, **changes: Any) -> dict[str, Any]:
        with self._lock, closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                job = self._load_job(connection, job_id)
                if job is None:
                    raise KeyError(job_id)
                job.update(changes, updated_at=time.time())
                connection.execute(
                    "UPDATE jobs SET state = ?, updated_at = ?, job_json = ? WHERE job_id = ?",
                    (job["state"], job["updated_at"], json.dumps(job, ensure_ascii=False), job_id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            self._write(job)
            return job

    def claim_next(self) -> dict[str, Any] | None:
        with self._lock, closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT job_id, job_json FROM jobs WHERE state = 'queued' ORDER BY created_at, job_id LIMIT 1"
                ).fetchone()
                if not row:
                    connection.commit()
                    return None
                job = json.loads(row["job_json"])
                job.update(state="processing", stage="planning", progress=10, updated_at=time.time())
                connection.execute(
                    "UPDATE jobs SET state = ?, updated_at = ?, job_json = ? WHERE job_id = ? AND state = 'queued'",
                    ("processing", job["updated_at"], json.dumps(job, ensure_ascii=False), row["job_id"]),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            self._write(job)
            return job

    def requeue_interrupted_jobs(self) -> int:
        """Return jobs left in processing to the durable queue after a restart."""
        recovered: list[dict[str, Any]] = []
        with self._lock, closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                rows = connection.execute("SELECT job_id, job_json FROM jobs WHERE state = 'processing'").fetchall()
                for row in rows:
                    job = json.loads(row["job_json"])
                    job.update(state="queued", stage="queued", progress=0, error=None, updated_at=time.time())
                    connection.execute(
                        "UPDATE jobs SET state = 'queued', updated_at = ?, job_json = ? WHERE job_id = ?",
                        (job["updated_at"], json.dumps(job, ensure_ascii=False), row["job_id"]),
                    )
                    recovered.append(job)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            for job in recovered:
                self._write(job)
        return len(recovered)

    def _write(self, job: dict[str, Any]) -> None:
        path = self.root / job["job_id"] / "job.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(job, indent=2, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)


class MPVEEngine:
    def __init__(
        self,
        output_root: str | Path = "build/mpve/jobs",
        store: JobStore | None = None,
        *,
        worker_count: int = 1,
        start_workers: bool = True,
        recover_interrupted: bool = True,
    ):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.store = store or JobStore(self.output_root)
        if worker_count < 1:
            raise ValueError("worker_count must be at least 1")
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._workers: list[threading.Thread] = []
        if recover_interrupted:
            self.store.requeue_interrupted_jobs()
        if start_workers:
            for index in range(worker_count):
                worker = threading.Thread(target=self._worker_loop, name=f"mpve-worker-{index + 1}", daemon=True)
                worker.start()
                self._workers.append(worker)

    def submit(self, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        request = VideoRequest.from_dict(payload)
        errors = request.validate()
        if errors:
            raise ValueError("; ".join(errors))
        job, duplicate = self.store.create(request)
        if not duplicate:
            self._wake_event.set()
        return job, duplicate

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            job = self.store.claim_next()
            if job is None:
                self._wake_event.wait(0.25)
                self._wake_event.clear()
                continue
            try:
                request = VideoRequest.from_dict(job["request"])
                self._run(job["job_id"], request)
            except Exception as exc:
                self.store.update(job["job_id"], state="failed", stage="failed", progress=100, error=str(exc))

    def close(self, *, wait: bool = True, timeout: float = 30.0) -> None:
        self._stop_event.set()
        self._wake_event.set()
        if wait:
            deadline = time.monotonic() + max(0.0, timeout)
            for worker in self._workers:
                worker.join(max(0.0, deadline - time.monotonic()))

    def _run(self, job_id: str, request: VideoRequest) -> None:
        try:
            self.store.update(job_id, state="processing", stage="planning", progress=10)
            storyboard = plan_storyboard(request)
            job_dir = self.output_root / job_id
            (job_dir / "storyboard.json").write_text(storyboard.to_json() + "\n", encoding="utf-8")
            self.store.update(job_id, stage="rendering", progress=30)
            output_path = job_dir / "video.mp4"
            result = render_hybrid(storyboard, output_path, fallback_dir=job_dir / "fallback", caption_words=list(request.caption_words))
            manifest_path = render_result_manifest(result, job_dir / "render.manifest.json")
            captions = None
            if request.caption_words:
                captions = write_sidecars([CaptionWord(str(item["text"]), int(item["start_ms"]), int(item["end_ms"]), bool(item.get("page_break_after", False))) for item in request.caption_words], job_dir / "captions", direction=request.caption_direction)
            expected_width, expected_height, expected_fps = (1920, 1080, 30) if result.provider == "remotion-cinematic" else (1280, 720, 24)
            qa = inspect_media(result.output_path, expected_duration=result.duration_seconds, expected_width=expected_width, expected_height=expected_height, expected_fps=expected_fps, sample_dir=job_dir / "qa-frames") if result.output_path and result.output_path.exists() else {"status": "fail", "errors": ["renderer did not produce an MP4"], "representative_frames": [], "audio_streams": []}
            review_path = write_final_review(qa, job_dir / "final-review.json", result.provider, result.duration_seconds, result.aspect_ratio)
            if result.output_path and result.output_path.exists() and qa["status"] == "pass":
                artifact = str(result.output_path)
                state = "completed"
                progress = 100
            else:
                artifact = None
                state = "failed"
                progress = 100
            result_payload = {
                "artifact": artifact,
                "manifest": str(manifest_path),
                "provider": result.provider,
                "duration_seconds": result.duration_seconds,
                "aspect_ratio": result.aspect_ratio,
                "audio": result.audio,
                "fallback_assets": [str(p) for p in result.fallback_assets],
                "errors": result.errors,
                "quality_gates": result.quality_gates,
                "storyboard": str(job_dir / "storyboard.json"),
                "qa": qa,
                "final_review": str(review_path),
                "captions": captions,
            }
            error = None if state == "completed" else "; ".join(qa.get("errors", [])) or "post-render QA failed"
            self.store.update(job_id, state=state, stage="completed" if state == "completed" else "failed", progress=progress, result=result_payload, error=error)
        except Exception as exc:
            self.store.update(job_id, state="failed", stage="failed", progress=100, error=str(exc))

    def status(self, job_id: str) -> dict[str, Any]:
        job = self.store.get(job_id)
        if not job:
            raise KeyError(job_id)
        return job

    def result(self, job_id: str) -> dict[str, Any]:
        job = self.status(job_id)
        if job["state"] != "completed":
            raise RuntimeError(f"job is {job['state']}; result is not available")
        return job
