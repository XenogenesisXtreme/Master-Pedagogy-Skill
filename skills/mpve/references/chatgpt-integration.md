# ChatGPT integration reference

Use MPVE as an attached capability of the existing MPS plugin. MPS remains the system of record for learner state, diagnosis, trigger decisions, teaching flow, and mastery.

## Adapter mapping

After MPS decides a video intervention is appropriate, map the current lesson into one request:

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
if learner_interest and analogy_permission:
    request["learner_interest"] = learner_interest
    request["analogy_consent"] = True
if learner.mode == "fhp":
    request["derived"] = written_derivation_completed
```

Do not set `analogy_consent` without explicit permission. Do not submit FHP until the written derivation is complete.

## Submit, poll, retrieve

```python
job_response = post_json("/videos", request)
job_id = job_response["job"]["job_id"]

while True:
    status = get_json(f"/videos/{job_id}")
    state = status["job"]["state"]
    if state in {"completed", "failed"}:
        break
    sleep(1)

if state == "completed":
    result = get_json(f"/videos/{job_id}/result")
    if result["result"].get("artifact"):
        present_video(result["result"]["artifact"], result["result"])
    else:
        explain_that_no_video_artifact_exists(result)
else:
    resume_written_explanation_with_retry_or_fallback(status)

resume_written_lesson_and_mastery_check()
```

A completed state requires real media QA and an existing artifact. Never present a storyboard, static fallback, mock URL, or failed job as a generated video. Treat fallback-only output as a capability limitation and return to the written lesson.

## Conversation behavior

When the learner asks for `video`, use Cinematic unless an explicit style is given. Do not ask for an exam profile for an isolated video request if topic signals can infer a presentation profile; do not persist that inference as the curriculum profile. Ask only for missing high-impact information such as duration, explicit analogy permission, or required accessibility constraints.

After video delivery, state what the video addressed, then continue MPS's explanation and ask the existing mastery question. Do not award XP, mastery, or a badge merely because the video was watched.
