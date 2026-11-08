#!/usr/bin/env python3
"""MPS-controlled remediation and recovery-video orchestration."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable

from scripts.mps_state import LearnerStateStore, LearnerSessionState


@dataclass(frozen=True)
class RecoveryResult:
    action: str
    concept_id: str
    incorrect_count: int
    diagnosis: dict[str, Any]
    video_request: dict[str, Any] | None = None
    job: dict[str, Any] | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "concept_id": self.concept_id,
            "incorrect_count": self.incorrect_count,
            "diagnosis": self.diagnosis,
            "video_request": self.video_request,
            "job": self.job,
            "message": self.message,
        }


class MPSRecoveryOrchestrator:
    """Coordinate recovery without letting MPVE diagnose or trigger itself.

    `video_decider` belongs to MPS and receives the diagnosed context. It must
    return whether motion/sequencing materially improves the remediation. The
    injected `submit_video` function can call MPVEEngine locally or an HTTP
    adapter; this class does not hardcode localhost or provider credentials.
    """

    def __init__(
        self,
        store: LearnerStateStore,
        *,
        video_decider: Callable[[dict[str, Any]], bool] | None = None,
        submit_video: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        self.store = store
        self.video_decider = video_decider or (lambda _context: False)
        self.submit_video = submit_video

    def record_answer(
        self,
        *,
        concept_id: str,
        correct: bool,
        topic: str,
        objective: str,
        mastery_check: str,
        misconception: str = "",
        subject: str = "Physics",
        subtopic: str = "",
        learner_level: str = "",
        prerequisites: tuple[str, ...] = (),
        exam_profile: str | None = None,
        mode: str = "standard",
        learner_interest: str | None = None,
        analogy_consent: bool = False,
        derived: bool = False,
    ) -> RecoveryResult:
        state = self.store.load()
        count = state.consecutive_incorrect.get(concept_id, 0)
        if correct:
            state.consecutive_incorrect[concept_id] = 0
            state.record_event("answer_correct", concept_id=concept_id)
            self.store.save(state)
            return RecoveryResult("continue", concept_id, 0, {}, message="Correct response; continue the mastery route.")

        count += 1
        state.consecutive_incorrect[concept_id] = count
        diagnosis = {
            "concept_id": concept_id,
            "misconception": misconception or "unresolved reasoning gap",
            "issue_type": self._issue_type(misconception),
            "subject": subject,
            "topic": topic,
        }
        state.misconceptions[concept_id] = diagnosis | {"last_count": count}
        state.record_event("answer_incorrect", concept_id=concept_id, count=count, diagnosis=diagnosis)
        if count < 3:
            self.store.save(state)
            return RecoveryResult("remediate_text", concept_id, count, diagnosis, message="Use a fresh explanation and test the same concept differently; do not trigger the primary recovery workflow yet.")

        recovery_key = self._recovery_key(concept_id, diagnosis)
        existing = state.video_jobs.get(recovery_key)
        if existing and existing.get("state") not in {"failed", "recovered"}:
            self.store.save(state)
            return RecoveryResult("await_video", concept_id, count, diagnosis, job=existing, message="A recovery intervention already exists for this misconception.")

        context = {
            "subject": subject, "topic": topic, "subtopic": subtopic,
            "objective": objective, "misconception": misconception,
            "mastery_check": mastery_check, "learner_level": learner_level,
            "prerequisites": list(prerequisites), "exam_profile": exam_profile,
            "mode": mode, "learner_interest": learner_interest,
            "analogy_consent": analogy_consent,
            "derived": derived,
            "incorrect_count": count, "diagnosis": diagnosis,
        }
        if mode.lower() in {"fhp", "floathead", "floathead physics"} and not derived:
            self.store.save(state)
            return RecoveryResult("continue_fhp_discovery", concept_id, count, diagnosis, message="Continue the FHP discovery and written derivation before requesting a video.")
        if not self.video_decider(context):
            state.record_event("video_declined_by_mps", concept_id=concept_id, recovery_key=recovery_key)
            self.store.save(state)
            return RecoveryResult("remediate_text", concept_id, count, diagnosis, message="MPS decided that text, a diagram, or another remediation is more appropriate than video.")

        request = {key: value for key, value in context.items() if key not in {"incorrect_count", "diagnosis"}}
        request.update({"style": "cinematic", "duration": 15, "aspect_ratio": "16:9"})
        job = None
        job_state = "approved"
        if self.submit_video:
            try:
                job = self.submit_video(request)
                job_state = job.get("state", "queued") if isinstance(job, dict) else "queued"
            except Exception as exc:
                job = {"state": "failed", "error": str(exc)}
                job_state = "failed"
        state.video_jobs[recovery_key] = {"state": job_state, "request": request, "job": job}
        state.record_event("video_requested", concept_id=concept_id, recovery_key=recovery_key, job=job)
        self.store.save(state)
        if job_state == "failed":
            return RecoveryResult("remediate_text", concept_id, count, diagnosis, request, job, "Video backend failed; continue with ordinary remediation.")
        return RecoveryResult("video_requested", concept_id, count, diagnosis, request, job, "MPS approved a visual intervention; resume the lesson after validated artifact delivery.")

    def complete_recovery(self, concept_id: str, *, success: bool, recovery_key: str | None = None) -> LearnerSessionState:
        state = self.store.load()
        state.consecutive_incorrect[concept_id] = 0 if success else state.consecutive_incorrect.get(concept_id, 0)
        if recovery_key and recovery_key in state.video_jobs:
            state.video_jobs[recovery_key]["state"] = "recovered" if success else "needs_rematch"
        state.record_event("recovery_completed", concept_id=concept_id, success=success)
        return self.store.save(state)

    def attach_video_status(self, recovery_key: str, status: dict[str, Any]) -> LearnerSessionState:
        state = self.store.load()
        if recovery_key not in state.video_jobs:
            raise KeyError(recovery_key)
        state.video_jobs[recovery_key]["job"] = status
        state.video_jobs[recovery_key]["state"] = status.get("state", state.video_jobs[recovery_key]["state"])
        state.record_event("video_status_updated", recovery_key=recovery_key, state=status.get("state"))
        return self.store.save(state)

    @staticmethod
    def _issue_type(misconception: str) -> str:
        value = misconception.lower()
        if any(token in value for token in ("algebra", "calculation", "sign", "unit")):
            return "mathematical"
        if any(token in value for token in ("prerequisite", "does not know", "forgot")):
            return "prerequisite"
        return "conceptual"

    @staticmethod
    def _recovery_key(concept_id: str, diagnosis: dict[str, Any]) -> str:
        payload = json.dumps({"concept_id": concept_id, "misconception": diagnosis.get("misconception", "")}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
