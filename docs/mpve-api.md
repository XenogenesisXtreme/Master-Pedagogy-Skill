# MPVE API

MPVE is a local video engine connected to the existing Master Pedagogy Skill. Start it with:

```bash
python scripts/mpve_server.py --host 127.0.0.1 --port 8787
```

By default, MPVE stores its SQLite database at `build/mpve/mpve.sqlite3` and job artifacts under `build/mpve/jobs/`. Use an explicit persistent directory and worker count for deployments:

```bash
python scripts/mpve_server.py --host 127.0.0.1 --port 8787 \
  --data-dir /srv/mpve --workers 2
```

The same settings are available through `MPVE_DATA_DIR` and `MPVE_WORKERS`. The data directory must be writable and remain available across service restarts. SQLite records are the source of truth; per-job `job.json` files are atomically replaced mirrors, and rendered media/caption artifacts live in each job's directory. On startup, jobs left in `processing` are returned to `queued` and may be rendered again. Keep this SQLite/WAL directory on local persistent storage and run one MPVE service instance per database; do not share it across hosts on a network filesystem. The legacy `--output-root` option still selects the jobs directory, with the database stored in its parent directory.

Loopback is the development default and does not require a token. For any non-loopback bind, configure a bearer token of at least 32 characters and TLS:

```bash
export MPVE_API_TOKEN='replace-with-a-long-random-secret'
python scripts/mpve_server.py --host 0.0.0.0 --port 8787 \
  --data-dir /srv/mpve --workers 2 \
  --tls-cert /etc/mpve/fullchain.pem --tls-key /etc/mpve/private-key.pem
```

The server compares the bearer token on each API request, limits each peer IP seen by MPVE to 120 requests per minute by default, and rejects bodies larger than 64 KiB. `--requests-per-minute` and `--max-request-bytes` configure those bounds. If requests pass through a reverse proxy, configure additional end-client rate limiting at the proxy. JSON is restricted to known fields, with per-field, prerequisite, and caption-word limits. `MPVEClient` sends `MPVE_API_TOKEN` automatically when set, or accepts `api_token=...` explicitly. For reverse-proxy deployments, keep the MPVE listener on loopback and configure the proxy to enforce HTTPS and pass the authorization header.

Completed and failed jobs have their original request payload removed from SQLite and `job.json`; active request data is retained only while needed to render or recover a queued job. Existing terminal rows are redacted at startup. Idempotency keys are stored as SHA-256 digests; startup migrates existing plaintext mappings. Terminal jobs and their artifact directories are purged after 30 days by default, on startup and hourly; configure `--retention-days` to change the period. Expired jobs are removed from the API and their idempotency mappings are released.

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
    "aspect_ratio": "16:9",
    "idempotency_key": "floatation-lesson-1"
  }'
```

Response status is `202` for a new job and `200` for a duplicate canonical request. The response contains `job.job_id`, `job.state`, `job.stage`, `job.progress`, and `job.request_fingerprint`, but does not echo the request payload. The optional `idempotency_key` may be reused with the same canonical request; reusing it with different request content returns `400`.

Submitting an identical request while its job is queued, processing, or completed returns that job. If it has failed, submitting it again creates a fresh job so transient renderer failures can be retried; this also works with the same idempotency key.

## Poll status

```bash
curl http://127.0.0.1:8787/videos/mps-abc123
```

The state is one of `queued`, `processing`, `completed`, or `failed`. Stage and progress are best-effort reporting fields. Errors are actionable strings; no placeholder URL is presented as a generated video.

## Retrieve the result

```bash
curl http://127.0.0.1:8787/videos/mps-abc123/result
```

The result includes a relative `result.artifact` URL when the Remotion or deterministic local renderer succeeds, selected provider, duration, aspect ratio, audio flag, errors, quality gates, and artifact-availability indicators. It omits host filesystem paths. Download the MP4 with `GET /videos/{job_id}/artifact`; this route follows the service's bearer-token policy (tokens are mandatory when configured) and only serves a completed MP4 resolved inside that job's directory. A result request before completion returns `409`.

When `caption_words` is supplied, each word must contain `text`, `start_ms`, and `end_ms`. MPVE writes SRT, WebVTT, and JSON timing sidecars under the job directory; the API reports available formats without disclosing local paths. `caption_direction` accepts `auto`, `ltr`, or `rtl`.

Before a job becomes `completed`, MPVE runs real post-render QA: ffprobe decoding, video stream, provider-specific dimension and frame-rate checks, duration validation, and four representative frame extractions. The API returns `result.qa` without filesystem paths or raw ffprobe output and indicates whether a final review is available. Invalid bytes or failed media checks produce a failed job even when a file exists.

## Integration contract

MPS owns the decision to call MPVE. A host adapter should:

1. Serialize the current topic, misconception, objective, learner context, and mastery check.
2. POST one request to `/videos`.
3. Poll the status endpoint or store the job ID for later retrieval.
4. Present the completed artifact only when `state=completed` and `result.artifact` exists.
5. Resume MPS's written explanation and mastery check after delivery.
6. Treat `failed` or fallback-only output as a recoverable capability issue, not as evidence of mastery.

The repository's [`scripts/mpve_client.py`](../scripts/mpve_client.py) implements bounded HTTP retries, stable idempotency for a submission attempt, status polling, timeout handling, and result retrieval. Inject `MPVEClient.submit` as the orchestrator's `submit_video` callback; pass terminal job/result data to `handle_video_status` so failed jobs resume text remediation and completed artifacts resume the mastery check.

The service is unauthenticated only on loopback unless `MPVE_API_TOKEN` is configured. Non-loopback binds require both a token and TLS certificate/key. Retention and artifact delivery are built in, but production deployments still need storage monitoring, secret rotation, backups, and operational monitoring. Configure `--data-dir` (or `MPVE_DATA_DIR`) to a persistent local volume rather than relying on the default build directory.
