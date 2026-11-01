# MPVE integration handoff for ChatGPT

The target architecture is one MPS plugin with an attached video capability. Do not expose MPVE as a separate tutoring product.

## Boundary

MPS remains the system of record for learner context, misconception diagnosis, the three-consecutive-incorrect-answer trigger, mode/profile decisions, follow-up teaching, and mastery. MPVE receives a structured request only after MPS decides a video intervention is appropriate.

## Adapter pseudocode

```python
request = {
    "topic": lesson.topic,
    "subtopic": lesson.subtopic,
    "learner_level": learner.level,
    "prerequisites": lesson.prerequisites,
    "misconception": diagnosis.primary_misconception,
    "objective": lesson.objective,
    "mastery_check": lesson.pending_mastery_question,
    "mode": learner.mode,
    "exam_profile": learner.primary_exam_profile,
    "style": "cinematic",
    "duration": 15,
    "aspect_ratio": "16:9",
}
job = post_json("/videos", request)
while True:
    status = get_json(f"/videos/{job['job']['job_id']}")
    if status["job"]["state"] in {"completed", "failed"}:
        break
    sleep(1)
if status["job"]["state"] == "completed":
    result = get_json(f"/videos/{job['job']['job_id']}/result")
    deliver(result["result"]["artifact"], result["result"])
resume_written_lesson_and_mastery_check()
```

Use `learner_interest` only when the learner has provided one and MPS has asked permission to use it in the video. Set `analogy_consent=true` only with that permission. For FHP, preserve the written derivation and pass `derived=true`; do not use MPVE to reveal a derivation before the learner has completed the FHP discovery stage.

## Error and fallback policy

A failed job should return to MPS's normal written explanation or a capability-specific retry path. A static fallback is an explicit scene-card artifact, not a genuine video; do not claim otherwise. The current local renderer is deterministic and may produce a silent MP4 when narration is unavailable. If production needs authentication, remote object storage, durable queues, or external providers, add them behind the MPVE API boundary rather than changing MPS pedagogy code.
