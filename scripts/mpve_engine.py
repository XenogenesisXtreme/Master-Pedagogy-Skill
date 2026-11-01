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
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.hybrid_video import render_hybrid, render_result_manifest
from scripts.video_explainer import build_storyboard

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
            idempotency_key=payload.get("idempotency_key"),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.topic:
            errors.append("topic is required")
        if not self.objective:
            errors.append("objective is required")
        if self.duration < 15 or self.duration > 45:
            errors.append("duration must be between 15 and 45 seconds")
        if self.aspect_ratio != "16:9":
            errors.append("aspect_ratio must be 16:9")
        if self.analogy_consent and not self.learner_interest:
            errors.append("learner_interest is required when analogy_consent is true")
        if self.mode.lower() in {"fhp", "floathead", "floathead physics"} and not self.derived:
            errors.append("FHP requests require derived=true after the written derivation is complete")
        return errors

    def canonical(self) -> dict[str, Any]:
        data = asdict(self)
        data["prerequisites"] = list(self.prerequisites)
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


def plan_storyboard(request: VideoRequest):
    narration = request.narration or _default_narration(request)
    equations = []
    if request.topic.lower().find("force") >= 0:
        equations.append("F = ma")
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
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._fingerprints: dict[str, str] = {}

    def create(self, request: VideoRequest) -> tuple[dict[str, Any], bool]:
        fingerprint = request.fingerprint()
        with self._lock:
            existing_id = self._fingerprints.get(fingerprint)
            if existing_id:
                return self._jobs[existing_id], True
            job_id = f"mps-{uuid.uuid4().hex[:12]}"
            job = {
                "job_id": job_id,
                "state": "queued",
                "stage": "queued",
                "progress": 0,
                "request": request.canonical(),
                "request_fingerprint": fingerprint,
                "created_at": time.time(),
                "updated_at": time.time(),
                "error": None,
                "result": None,
            }
            self._jobs[job_id] = job
            self._fingerprints[fingerprint] = job_id
            self._write(job)
            return job, False

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: Any) -> dict[str, Any]:
        with self._lock:
            job = self._jobs[job_id]
            job.update(changes, updated_at=time.time())
            self._write(job)
            return job

    def _write(self, job: dict[str, Any]) -> None:
        path = self.root / job["job_id"] / "job.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class MPVEEngine:
    def __init__(self, output_root: str | Path = "build/mpve/jobs", store: JobStore | None = None):
        self.output_root = Path(output_root)
        self.store = store or JobStore(self.output_root)

    def submit(self, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        request = VideoRequest.from_dict(payload)
        errors = request.validate()
        if errors:
            raise ValueError("; ".join(errors))
        job, duplicate = self.store.create(request)
        if not duplicate:
            thread = threading.Thread(target=self._run, args=(job["job_id"], request), daemon=True)
            thread.start()
        return job, duplicate

    def _run(self, job_id: str, request: VideoRequest) -> None:
        try:
            self.store.update(job_id, state="processing", stage="planning", progress=10)
            storyboard = plan_storyboard(request)
            job_dir = self.output_root / job_id
            (job_dir / "storyboard.json").write_text(storyboard.to_json() + "\n", encoding="utf-8")
            self.store.update(job_id, stage="rendering", progress=30)
            output_path = job_dir / "video.mp4"
            result = render_hybrid(storyboard, output_path, fallback_dir=job_dir / "fallback")
            manifest_path = render_result_manifest(result, job_dir / "render.manifest.json")
            if result.output_path and result.output_path.exists():
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
            }
            self.store.update(job_id, state=state, stage="completed" if state == "completed" else "failed", progress=progress, result=result_payload, error=None if state == "completed" else "renderer did not produce an MP4")
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
