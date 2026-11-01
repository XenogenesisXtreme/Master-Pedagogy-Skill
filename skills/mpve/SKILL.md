---
name: mpve
description: Master Pedagogy Video Engine workflow for planning, rendering, validating, and delivering instructional videos inside the existing MPS plugin. Use when MPS has already decided that a video intervention is appropriate or when implementing/testing the MPVE API.
---

# Master Pedagogy Video Engine

MPVE is a video-generation capability inside Master Pedagogy, not a separate user-facing plugin. Preserve the existing MPS conversation, learner state, misconception diagnosis, trigger decisions, follow-up questions, and mastery gates.

## Responsibility boundary

MPS decides whether a video is appropriate, supplies structured learning context, and resumes teaching and mastery checking after the video. MPVE owns video planning, script/storyboard construction, visuals, equations/diagrams, narration/captions when configured, rendering, QA, job lifecycle, and artifact delivery. MPVE must not invent a pedagogical trigger or replace a mastery check.

## Request contract

Submit JSON containing at least `topic` and `objective`. Useful fields include `subtopic`, `learner_level`, `prerequisites`, `misconception`, `mastery_check`, `exam_profile`, `mode`, `style`, `duration`, `aspect_ratio`, `narration`, `learner_interest`, `analogy_consent`, and `derived`.

Cinematic is the default style. The current local renderer requires 16:9 and a 15–45 second duration. FHP requests require `derived: true` because the video reinforces a completed written derivation and must not replace first-principles discovery. Use learner interests only when MPS has obtained consent.

## API

Run `python scripts/mpve_server.py --port 8787`.

- `POST /videos` creates a job and returns a job ID. Identical canonical requests are deduplicated.
- `GET /videos/{job_id}` returns `queued`, `processing`, `completed`, or `failed` state, stage, progress, and errors.
- `GET /videos/{job_id}/result` returns the final artifact and metadata after completion; it returns a conflict while the job is not complete.

The current provider order is local deterministic Cinematic MP4 rendering, then the existing optional hosted adapter hook, then checked SVG fallback. A fallback is reported explicitly and must never be described as a genuine MP4.

## Operational workflow

1. Receive a valid request from MPS.
2. Validate required fields, duration, aspect ratio, FHP derivation state, and analogy consent.
3. Create a storyboard before rendering and persist it with the job.
4. Render through the provider boundary.
5. Write a render manifest with provider, artifact, duration, audio, fallback assets, errors, and quality gates.
6. Return the artifact and metadata to MPS.
7. MPS resumes its written explanation and mastery check; MPVE does not mark mastery.

Use `scripts/mpve_engine.py` for library integration and `scripts/mpve_server.py` for the local HTTP adapter. Keep provider-specific additions behind the renderer boundary and retain structured errors, idempotency, and artifact paths.

## Verification

Run the MPVE tests and an end-to-end sample. Check that the output is a real playable MP4 with H.264 video, 1280×720 dimensions, the requested duration range, and a manifest. Also test invalid requests, duplicate submission, status polling, result-before-completion behavior, and renderer failure reporting.
