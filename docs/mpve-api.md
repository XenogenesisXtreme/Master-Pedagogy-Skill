# MPVE API

MPVE is a local video engine connected to the existing Master Pedagogy Skill. Start it with:

```bash
python scripts/mpve_server.py --host 127.0.0.1 --port 8787
```

## Submit a video

```bash
curl -X POST http://127.0.0.1:8787/videos \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "Floatation",
    "subtopic": "buoyant force",
    "objective": "Explain why an object floats when buoyant force balances its weight",
    "misconception": "A heavier object must always sink",
    "learner_level": "NEET",
    "mastery_check": "Predict what happens when displaced volume increases",
    "duration": 15,
    "style": "cinematic",
    "aspect_ratio": "16:9"
  }'
```

Response status is `202` for a new job and `200` for a duplicate canonical request. The response contains `job.job_id`, `job.state`, `job.stage`, `job.progress`, and `job.request_fingerprint`.

## Poll status

```bash
curl http://127.0.0.1:8787/videos/mps-abc123
```

The state is one of `queued`, `processing`, `completed`, or `failed`. Stage and progress are best-effort reporting fields. Errors are actionable strings; no placeholder URL is presented as a generated video.

## Retrieve the result

```bash
curl http://127.0.0.1:8787/videos/mps-abc123/result
```

The result includes the MP4 path when the local renderer succeeds, the storyboard path, render manifest path, selected provider, duration, aspect ratio, audio flag, fallback assets, errors, and quality gates. A result request before completion returns `409`.

When `caption_words` is supplied, each word must contain `text`, `start_ms`, and `end_ms`. MPVE writes SRT, WebVTT, and JSON timing sidecars under the job directory and returns their paths in `result.captions`. `caption_direction` accepts `auto`, `ltr`, or `rtl`.

Before a job becomes `completed`, MPVE runs real post-render QA: ffprobe decoding, video stream and dimension checks, duration validation, and four representative frame extractions. The result contains `result.qa` and a `result.final_review` path. Invalid bytes or failed media checks produce a failed job even when a file exists.

## Integration contract

MPS owns the decision to call MPVE. A host adapter should:

1. Serialize the current topic, misconception, objective, learner context, and mastery check.
2. POST one request to `/videos`.
3. Poll the status endpoint or store the job ID for later retrieval.
4. Present the completed artifact only when `state=completed` and `result.artifact` exists.
5. Resume MPS's written explanation and mastery check after delivery.
6. Treat `failed` or fallback-only output as a recoverable capability issue, not as evidence of mastery.

The service currently stores jobs under `build/mpve/jobs`. Production deployments should replace this with a configured persistent storage and authenticated network boundary.
