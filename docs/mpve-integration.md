# MPVE integration handoff for ChatGPT

The target architecture is one MPS plugin with an attached video capability. Do not expose MPVE as a separate tutoring product.

## Boundary

MPS remains the system of record for learner context, misconception diagnosis, the three-consecutive-incorrect-answer trigger, mode/profile decisions, follow-up teaching, and mastery. MPVE receives a structured request only after MPS decides a video intervention is appropriate. The repository includes an HTTP client and a local API server; a host still supplies its real MPS video decision and deployment configuration.

## Python adapter flow

`MPVEClient.submit` can be injected directly into `MPSRecoveryOrchestrator`. The orchestrator adds a stable idempotency key, calls the adapter only after MPS approves video, and keeps a recovery key for later status updates.

```python
import os

from scripts.intervention_orchestrator import MPSRecoveryOrchestrator
from scripts.mpve_client import MPVEClient, MPVEJobFailed, MPVETimeoutError
from scripts.mps_state import LearnerStateStore

client = MPVEClient(
    os.environ.get("MPVE_BASE_URL", "http://127.0.0.1:8787"),
    request_timeout=10,
    job_timeout=180,
    poll_interval=1,
    max_retries=2,
)
store = LearnerStateStore("data/learner.json")
orchestrator = MPSRecoveryOrchestrator(
    store,
    video_decider=mps_video_decider,  # owned by MPS; do not always approve video
    submit_video=client.submit,
)

recovery = orchestrator.record_answer(
    concept_id=lesson.concept_id,
    correct=answer_is_correct,
    subject=lesson.subject,
    topic=lesson.topic,
    subtopic=lesson.subtopic,
    objective=lesson.objective,
    misconception=diagnosis.primary_misconception,
    mastery_check=lesson.pending_mastery_question,
    learner_level=learner.level,
    prerequisites=tuple(lesson.prerequisites),
    exam_profile=learner.primary_exam_profile,
    mode=learner.mode,
    learner_interest=learner.interest_if_consented,
    analogy_consent=learner.consented_to_interest_analogy,
    derived=lesson.fhp_derivation_completed,
)

if recovery.action == "video_requested":
    job_id = recovery.job["job_id"]
    try:
        delivery = client.wait_for_result(job_id)
    except MPVEJobFailed as error:
        next_step = orchestrator.handle_video_status(recovery.recovery_key, error.job)
        # next_step.action is remediate_text; continue with ordinary MPS teaching.
    except MPVETimeoutError as timeout:
        next_step = orchestrator.handle_video_status(recovery.recovery_key, timeout.job)
        # Keep the job ID and resume polling later; a timeout is not a render failure.
    else:
        next_step = orchestrator.handle_video_status(recovery.recovery_key, delivery)
        if next_step.action == "await_mastery_check":
            deliver_to_learner(delivery["result"]["artifact"])
            passed = assess_mastery(lesson.pending_mastery_question)
            orchestrator.complete_recovery(
                lesson.concept_id,
                success=passed,
                recovery_key=recovery.recovery_key,
            )
```

The `recovery.action` value is the routing contract: `remediate_text` continues with text when the MPS decision declines video, no adapter is configured, submission fails, or a job fails/has no artifact; `await_video` means poll later; `await_mastery_check` means a completed artifact is ready but mastery is not yet established. Only the actual follow-up assessment may close recovery as successful.

## Retry and timeout behavior

`MPVEClient` uses the Python standard library. POST retries reuse one idempotency key, retry only transient transport errors and selected HTTP status codes, and stop after a bounded number of attempts. The orchestrator derives a stable key for the exact recovery request, allowing failed jobs to be retried without confusing a changed request with the original. Polling is bounded; `MPVETimeoutError.job` preserves the latest status so the host can resume rather than incorrectly mark the job failed. `MPVEJobFailed.job` can be passed to `handle_video_status` to select the text fallback.

## Learner consent and FHP safeguards

Use `learner_interest` only when the learner has provided an interest and MPS has asked permission to use it in the video. Set `analogy_consent=True` only with that permission. For FHP, preserve the written derivation and pass `derived=True`; do not use MPVE to reveal a derivation before the learner has completed the FHP discovery stage.

## Error, security, and deployment policy

A failed job should return to MPS's normal written explanation or an explicit retry path. A static fallback is a scene-card artifact, not a genuine video; do not claim otherwise. Present a video only when the job is `completed`, a result artifact exists, and MPVE's QA has passed. The provider order is Remotion Cinematic, deterministic local Cinematic, optional hosted adapter, then SVG fallback. Remotion produces a genuine 1920×1080 MP4 and may produce silent audio when narration/TTS is unavailable.

The local API currently has no authentication and the job index is in memory, even though job artifacts are written to disk. Do not expose it publicly as-is. Production deployments should add authenticated HTTPS, durable job state/queueing, controlled artifact storage and retention, request limits, and secret handling behind the MPVE API boundary rather than changing MPS pedagogy decisions.
